from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from fmh import model


class DownloadController(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, key):
        file = model.File.get_by_key(key)
        blob = blobstore.BlobInfo.get(file.file_key)
        # Update statistics.
        if not file.download_count: file.download_count = 0
        if not file.download_bytes: file.download_bytes = 0
        file.download_count += 1
        file.download_bytes += blob.size
        file.put()
        # Send the file.
        self.send_blob(blob)
