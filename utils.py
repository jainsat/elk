import os
import tarfile
import logging

class Utils:

    @staticmethod
    def extract_tgz_file(filename, dest_dir):
        assert Utils.is_tar_gzipped(filename), \
            'Invalid file extension: Expected .tgz or .tar.gz, found {0}'.format(filename)
        tar = tarfile.open(filename, 'r:gz')
        if dest_dir is None:
            dest_dir = os.getcwd()
        tar.extractall(path=dest_dir)
        top_dir = os.path.commonprefix(tar.getnames())
        tar.close()
        logging.debug("Done extracting {0}".format(filename))
        return top_dir

    @staticmethod
    def is_tar_gzipped(filename):
        return filename.endswith(".tgz") or filename.endswith(".tar.gz")

    @staticmethod
    def is_nsx_manager_support_bundle(filename):
        return filename.startswith("nsx_manager_") and Utils.is_tar_gzipped(filename)