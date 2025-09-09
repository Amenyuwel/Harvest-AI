import logging

class Notifier:
    def __init__(self):
        self.logger = logging.getLogger("Notifier")

    def notify_admin(self, message: str):
        """
        Notify admin (for now, just log).
        Can be extended to send email, Telegram, or PocketBase push.
        """
        self.logger.info(f"[ADMIN NOTIFY] {message}")
        print(f"[ADMIN NOTIFY] {message}")  # console feedback too
