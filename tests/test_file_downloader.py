"""Tests for file downloader security and path logic."""

from __future__ import annotations

import unittest

from src.extractors.file_downloader import FileDownloader, _validate_url


class ValidateUrlTests(unittest.TestCase):
    def test_allows_https(self) -> None:
        _validate_url("https://example.com/file.zip")  # should not raise

    def test_allows_http(self) -> None:
        _validate_url("http://example.com/file.zip")  # should not raise

    def test_blocks_file_scheme(self) -> None:
        with self.assertRaises(ValueError):
            _validate_url("file:///etc/passwd")

    def test_blocks_ftp_scheme(self) -> None:
        with self.assertRaises(ValueError):
            _validate_url("ftp://evil.com/file")

    def test_blocks_empty_scheme(self) -> None:
        with self.assertRaises(ValueError):
            _validate_url("://noscheme")

    def test_blocks_no_hostname(self) -> None:
        with self.assertRaises(ValueError):
            _validate_url("https://")


class FileDownloaderPathTests(unittest.TestCase):
    def test_target_path_deterministic_fallback(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            dl = FileDownloader(download_directory=td)
            path1 = dl._target_path(None, "https://example.com/")
            path2 = dl._target_path(None, "https://example.com/")
            self.assertEqual(path1, path2)

    def test_target_path_uses_filename(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            dl = FileDownloader(download_directory=td)
            path = dl._target_path("my_file.csv", "https://example.com/data")
            self.assertEqual(path.name, "my_file.csv")


if __name__ == "__main__":
    unittest.main()
