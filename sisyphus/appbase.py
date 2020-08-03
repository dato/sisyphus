from pydantic import BaseSettings, SecretStr


class GithubApp(BaseSettings):
    """Clase para configurar flask_githubapp.
    """

    app_id: int
    key_path: str
    endpoint: str
    webhook_secret: SecretStr

    def flask_config(self):
        return dict(
            GITHUBAPP_ID=self.app_id,
            GITHUBAPP_ROUTE=self.endpoint,
            GITHUBAPP_SECRET=self.webhook_secret.get_secret_value(),
            GITHUBAPP_KEY=open(self.key_path, "rb").read(),
        )
