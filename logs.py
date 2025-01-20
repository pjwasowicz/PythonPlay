import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# Pobierz katalog domowy użytkownika
user_home_dir = os.path.expanduser("~")
log_dir = os.path.join(user_home_dir, "milonga_logs")

# Upewnij się, że katalog logów istnieje
os.makedirs(log_dir, exist_ok=True)

# Ścieżka do pliku logu
log_file_path = os.path.join(log_dir, "milonga.log")

# Konfiguracja loggera
logger = logging.getLogger("Milonga: ")
logger.setLevel(logging.DEBUG)

# Utwórz i skonfiguruj TimedRotatingFileHandler dla miesięcznej rotacji
handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=12)
handler.suffix = "%Y-%m"  # Dodaj datę do nazwy pliku logu
handler.setLevel(logging.DEBUG)

# Formatowanie logów
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Dodaj handler do loggera
logger.addHandler(handler)

# Klasa przechwytująca wyjścia i przekierowująca do loggera oraz do oryginalnych strumieni
class LoggerWriter:
    def __init__(self, logger, level, original_stream):
        self.logger = logger
        self.level = level
        self.original_stream = original_stream

    def write(self, message):
        if message.strip() != "":
            # Dodaj znak nowej linii na końcu każdej wiadomości
            self.logger.log(self.level, message.strip())
            self.original_stream.write(message.strip() + '\n')
            self.original_stream.flush()

    def flush(self):
        self.original_stream.flush()

# Przechwycenie printów i błędów
sys.stdout = LoggerWriter(logger, logging.INFO, sys.stdout)
sys.stderr = LoggerWriter(logger, logging.ERROR, sys.stderr)

# Przykładowe użycie
#print("To jest informacja")
#raise Exception("To jest błąd")