import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from jinja2 import Environment, FileSystemLoader
from src.exceptions.email import BaseEmailError


logger = logging.getLogger(__name__)


class EmailSenderService:
    def __init__(
            self,
            hostname: str,
            port: int,
            email: str,
            password: str,
            use_tls: bool,
            template_dir: str,
            activation_email_template_name: str,
            activation_complete_email_template_name: str,
            password_email_template_name: str,
            password_complete_email_template_name: str,
    ):
        self._hostname = hostname
        self._port = port
        self._email = email
        self._password = password
        self._use_tls = use_tls
        self._activation_email_template_name = activation_email_template_name
        self._activation_complete_email_template_name = activation_complete_email_template_name
        self._password_email_template_name = password_email_template_name
        self._password_complete_email_template_name = password_complete_email_template_name

        logger.info(
            f"Initializing EmailSenderService with hostname={hostname}, port={port}, email={email}, use_tls={use_tls}, template_dir={template_dir}")

        try:
            self._env = Environment(loader=FileSystemLoader(template_dir))
            logger.info(f"Successfully initialized Jinja2 environment with template_dir={template_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize Jinja2 environment: {e}", exc_info=True)
            raise

    async def _send_email(self, recipient: str, subject: str, html_content: str) -> None:
        """
        Asynchronously send an email with the given subject and HTML content.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            html_content (str): The HTML content of the email.

        Raises:
            BaseEmailError: If sending the email fails.
        """
        logger.info(f"Sending email to {recipient} with subject: {subject}")

        message = MIMEMultipart()
        message["From"] = self._email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))

        try:
            smtp = aiosmtplib.SMTP(hostname=self._hostname, port=self._port, use_tls=self._use_tls)
            logger.debug(f"Connecting to SMTP server {self._hostname}:{self._port} with use_tls={self._use_tls}")
            await smtp.connect()
            if self._use_tls:
                logger.debug("Initiating STARTTLS for port 587")
                await smtp.starttls()
            logger.debug(f"Logging in with email {self._email}")
            await smtp.login(self._email, self._password)
            logger.debug(f"Sending email to {recipient}")
            await smtp.sendmail(self._email, [recipient], message.as_string())
            await smtp.quit()
            logger.info(f"Successfully sent email to {recipient} with subject: {subject}")
        except aiosmtplib.SMTPException as error:
            logger.error(f"SMTP error sending email to {recipient}: {error}", exc_info=True)
            raise BaseEmailError(f"SMTP error: {error}")
        except Exception as error:
            logger.error(f"Unexpected error sending email to {recipient}: {error}", exc_info=True)
            raise BaseEmailError(f"Unexpected error: {error}")

    async def send_activation_email(self, email: str, activation_link: str) -> None:
        logger.info(f"Preparing activation email for {email} with link: {activation_link}")
        try:
            template = self._env.get_template(self._activation_email_template_name)
            html_content = template.render(email=email, activation_link=activation_link)
            subject = "Account Activation"
            await self._send_email(email, subject, html_content)
            logger.info(f"Activation email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send activation email to {email}: {e}", exc_info=True)
            raise

    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        logger.info(f"Preparing activation complete email for {email} with link: {login_link}")
        try:
            template = self._env.get_template(self._activation_complete_email_template_name)
            html_content = template.render(email=email, login_link=login_link)
            subject = "Account Activated Successfully"
            await self._send_email(email, subject, html_content)
            logger.info(f"Activation complete email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send activation complete email to {email}: {e}", exc_info=True)
            raise

    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        logger.info(f"Preparing password reset email for {email} with link: {reset_link}")
        try:
            template = self._env.get_template(self._password_email_template_name)
            html_content = template.render(email=email, reset_link=reset_link)
            subject = "Password Reset Request"
            await self._send_email(email, subject, html_content)
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}", exc_info=True)
            raise

    async def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        logger.info(f"Preparing password reset complete email for {email} with link: {login_link}")
        try:
            template = self._env.get_template(self._password_complete_email_template_name)
            html_content = template.render(email=email, login_link=login_link)
            subject = "Your Password Has Been Successfully Reset"
            await self._send_email(email, subject, html_content)
            logger.info(f"Password reset complete email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send password reset complete email to {email}: {e}", exc_info=True)
            raise