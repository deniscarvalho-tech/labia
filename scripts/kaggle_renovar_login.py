"""Renova a credencial OAuth do Kaggle (contorno de um defeito do cliente kaggle 2.2.5).

O cliente acha que a credencial ainda vale quando ela já venceu (a validade é de 12 horas), não a renova
e cai no modo anônimo, que não enxerga notebooks privados. O sintoma é a mensagem
"Permission 'kernels.get' was denied" num notebook que é seu.

Rode com o Python do próprio cliente do Kaggle (ele tem a biblioteca kagglesdk):

    & "$env:APPDATA\\uv\\tools\\kaggle\\Scripts\\python.exe" scripts/kaggle_renovar_login.py

Nenhum token é impresso.
"""

from kagglesdk import KaggleClient
from kagglesdk.kaggle_creds import KaggleCredentials

with KaggleClient() as client:
    creds = KaggleCredentials.load(client=client)
    if creds is None:
        raise SystemExit("nenhuma credencial salva: rode `kaggle auth login`")
    creds.refresh_access_token()
    creds.save()
    print(
        f"credencial de {creds.get_username()} renovada; vale até {creds._access_token_expiration:%d/%m %H:%M} UTC"
    )
