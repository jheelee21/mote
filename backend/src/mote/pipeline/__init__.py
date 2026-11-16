"""Indexing pipeline.

Rule: modules here are pure functions over files, images and arrays. They must
not import FastAPI or `mote.db`; `mote.jobs` connects them to storage.

Stages: scan → thumbs → exif → embed → signals → cluster → naming.
"""
