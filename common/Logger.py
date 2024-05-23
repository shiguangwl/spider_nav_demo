import logging
import os

class CustomLogger:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # 创建一个日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)-8s')

        # 创建一个文件处理器，用于将日志写入到文件中
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 创建一个控制台处理器，用于将日志输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, error=None):
        if error:
            message += f" Error: {error}"
        self.logger.error(message)

logger = CustomLogger("../app.log")

if __name__ == "__main__":
    # 设置日志文件路径
    log_file_path = "../app.log"

    # 实例化日志工具类
    logger = CustomLogger(log_file_path)

    # 记录不同级别的日志信息
    logger.info("This is an informational message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.error("This is another error message with more details.", error="Some details here.")
