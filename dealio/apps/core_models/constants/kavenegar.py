class KavenegarConfig:
    API_KEY: str = '4C57563538454343305576754669433775334F3047627A732F335A4E39576F385372304F6D446E696855413D'
    base_url: str = "https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json?receptor={receptor}&token={token_value}&token2={token2}&template={template}"
    # change_password_url: str = "https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json?receptor={receptor}&token={token_value}&template={template}"
