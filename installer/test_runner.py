"""Verifica preservação de dados e escolha de porta sem instalar pacotes reais."""

import importlib.util
import socket
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "forum_installer_runner", Path(__file__).with_name("runner.py")
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class InstallerTests(unittest.TestCase):
    def test_backup_includes_committed_wal(self):
        with tempfile.TemporaryDirectory(prefix="Fórum com espaços ") as directory:
            root = Path(directory)
            source = root / "db.sqlite3"
            with sqlite3.connect(source) as database:
                database.execute("PRAGMA journal_mode=WAL")
                database.execute("CREATE TABLE carteira (saldo INTEGER)")
                database.execute("INSERT INTO carteira VALUES (180)")
                database.commit()
                backup = runner.backup_database(source, root / "backups")
                with sqlite3.connect(backup) as copy:
                    self.assertEqual(
                        copy.execute("SELECT saldo FROM carteira").fetchone(), (180,)
                    )
                self.assertEqual(
                    database.execute("SELECT saldo FROM carteira").fetchone(), (180,)
                )

    def test_busy_port_chooses_another(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            original = occupied.getsockname()[1]
            selected = runner.available_port(original)
            self.assertNotEqual(selected, original)
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", selected))

    def test_downgraded_dependency_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.txt"
            path.write_text("Django==5.2.18\n", encoding="utf-8")
            with patch.object(
                runner.importlib.metadata, "version", return_value="4.2.30"
            ):
                self.assertFalse(runner.requirements_match(path))
            with patch.object(
                runner.importlib.metadata, "version", return_value="5.2.18"
            ):
                self.assertTrue(runner.requirements_match(path))


if __name__ == "__main__":
    unittest.main()
