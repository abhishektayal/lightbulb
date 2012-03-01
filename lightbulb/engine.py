# -*- coding: utf-8 -*-
#
# Copyright 2012 James Thornton (http://jamesthornton.com)
# BSD License (see LICENSE for details)
#
import os
import docutils
import docutils.core
from datetime import datetime
from fnmatch import fnmatch


class Config(object):
    
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or os.getcwd()
        self.source_folder = "source"
        self.build_folder = "build"
        self.timezone = "America/Chicago"
        #self.current_directory = os.getcwd()

class Source(object):

    def __init__(self, config):
        self.config = config
        self.source_dir = "%s/%s" % (config.project_dir, config.source_folder)
        self.writer_name = 'html4css1'

    # Builder
    def get_fragment(self, source_abspath):
        source = self.get_document_source(source_abspath)
        parts = self.get_document_parts(source) 
        return parts['fragment']

    # Loader
    def get_data(self, source_abspath):
        source = self.get_document_source(source_abspath)
        parts = self.get_document_parts(source) 

        data = dict()
        data['title'] = parts['title']
        data['subtitle'] = parts['subtitle']
        data['fragment'] = parts['fragment']
        
        # Extra metadata: docid, author, date, tags
        meta = self._get_metadata(source, source_abspath) 
        data.update(meta)  

        # Derived parts: slug, fragment_path, source_path 
        slug = self.get_slug(source_abspath)
        data['slug'] = slug
        data['fragment_path'] = self.get_fragment_path(source_abspath)
        data['source_path'] = self.get_source_path(source_abspath)

        return data

    # Source
    def get_document_source(self, source_abspath):
        def_source = self.get_substitution_definitions()
        doc_source = self.read_source_file(source_abspath)
        source = "\n".join([def_source, doc_source])
        return source
                
    # Source
    def get_document_parts(self, source):
        # http://docutils.sourceforge.net/docs/api/publisher.html#publish-parts-details
        settings = dict(initial_header_level=2) # do we need this?
        options = dict(source=source, writer_name=self.writer_name, settings_overrides=settings)
        parts = docutils.core.publish_parts(**options)
        return parts
    
    # Source
    def get_substitution_definitions(self):
        # Standard substitution definitions
        # http://docutils.sourceforge.net/docs/ref/rst/definitions.html
        target_filename = "substitutions.rst"
        current_dir = os.path.dirname(__file__)
        source_abspath = os.path.normpath(os.path.join(current_dir, target_filename))
        source = self.read_source_file(source_abspath)
        return source

    # Source
    def read_source_file(self,source_abspath):
        fin = open(source_abspath, "r")
        source = fin.read().decode('utf-8')
        return source       

    # Source
    def get_slug(self, source_abspath):
        start = self.get_source_dir()
        #relative_path = file_name.rpartition(source_dir)[-1].lstrip("/") 
        relative_path = os.path.relpath(source_abspath, start)
        slug = os.path.splitext(relative_path)[0]
        return slug

    # Source
    def get_source_dir(self):
        source_dir = os.path.join(self.config.project_dir, self.config.source_folder)
        return source_dir

    
    #def get_source_abspath(self, file_name):
    #    source_abspath = os.path.join(self.config.project_dir, self.config.source_folder, file_name)
    #    return source_abspath
     
    # Source
    def get_source_path(self, source_abspath):
        #source_path = os.path.join(self.config.source_folder, file_name)
        #return source_path
        start = self.config.project_dir
        source_path = os.path.relpath(source_abspath, start)
        return source_path

    #def get_fragment_dir(self)
    #    fagment_dir = os.path.join(self.config.project_dir, self.config.build_folder)
    #    return fragment_dir

    # Builder
    def get_fragment_abspath(self, source_abspath):
        fragment_path = self.get_fragment_path(source_abspath)
        return os.path.join(self.config.project_dir, fragment_path)

    # Source
    def get_fragment_path(self, source_abspath):
        # /project/source/2012/hello.rst => /project/source/2012, hello.rst
        head_dir, basename = os.path.split(source_abspath)

        # /project/source/2012 => 2012 
        start = self.get_source_dir()
        fragment_folder = os.path.relpath(head_dir, start)

        # hello.rst ==> hello
        stub = os.path.splitext(basename)[0]  # remove the ext
        filename = "%s.html" % stub        

        # ==> build/2012/hello.html
        fragment_path = os.path.join(self.config.build_folder, fragment_folder, filename)
        return os.path.normpath(fragment_path)

        
        
    # Source
    def _get_metadata(self, source, source_abspath):
        doctree = docutils.core.publish_doctree(source)
        docinfo = doctree.traverse(docutils.nodes.docinfo)
        try:
            meta = self._process_standard_fields(docinfo)
            meta = self._process_custom_fields(meta)
        except IndexError:
            print "ERROR: Source file is missing data: %s" % source_abspath
            raise
        for key, value in meta.items():
            meta[key] = value.astext()
        return meta

    # Source
    def _process_standard_fields(self,docinfo):
        # Standard fields: date, author, etc.
        meta = {}
        for node in docinfo[0].children:
            key = node.tagname.lower()
            value = node.children[0]
            meta[key] = value
        return meta

    # Source
    def _process_custom_fields(self, meta):
        # http://repo.or.cz/w/wrigit.git/blob/f045e5e7766e767c0b56bcb7a1ba0582a6f4f176:/rst.py
        field = meta['field']
        meta['tags'] = field.parent.children[1]
        meta['docid'] = field.parent.parent.children[0].children[1]
        del meta['field']
        return meta
        
    # Builder, Loader
    def get_all_files(self):
        source_dir = self.get_source_dir()
        for root, dirs, files in os.walk(source_dir):
            for filename in files:
                # Ignore pattern: emacs autosave files. TODO: generalize this
                if fnmatch(filename, "*.rst") and not fnmatch(filename, "*.#*"):
                    source_abspath = os.path.join(root, filename)
                    yield source_abspath


class Builder(object):
    def __init__(self, config):
        self.config = config
        self.source = Source(config)

    def run(self):
        for source_abspath in self.source.get_all_files():
            fragment = self.source.get_fragment(source_abspath)
            fragment_abspath = self.source.get_fragment_abspath(source_abspath)
            self.write_fragment(fragment, fragment_abspath)
        print "Done."

    def write_fragment(self, fragment, fragment_abspath):
        with self.open_fragment_file(fragment_abspath) as fout:
            fout.write(fragment.encode('utf-8') + '\n')
 
    def open_fragment_file(self, fragment_abspath):
        self.make_fragment_folder(fragment_abspath)
        return open(fragment_abspath, "w")

    def make_fragment_folder(self, fragment_abspath):
        fragment_dir = os.path.dirname(fragment_abspath)
        if not os.path.isdir(fragment_folder):
            os.makedirs(fragment_folder)


class Loader(object):

    def __init__(self, graph, changelog, config):
        self.graph = graph
        self.changelog = changelog
        self.config = config
        self.source = Source(self.config)

    def save(self):
        log = self.changelog.get()
        for filename in log:
            status, timestamp = log[filename]
            print status, filename, timestamp
            #data = self.source.get_data(filename)
            #entry = self.graph.entries.create(data)
            #print entry.eid, entry.map()
          
    def update_all(self):
        for source_abspath in self.source.get_all_files():
            data = self.source.get_data(source_abspath)
            # TODO: if fragment exists...
            entry = self.graph.entries.save(data)
            print entry.eid, entry.map()

    def get_last_updated(self):
        # Get the lightbulb metadata node for entries
        meta = self.graph.lightbulb.get_or_create(name="entries")        
        return meta.get('last_updated')
       
    def set_last_updated(self, last_updated):
        # Get the lightbulb metadata node for entries
        meta = self.graph.lightbulb.get_or_create(name="entries")
        meta.last_updated = last_updated
        meta.save()

