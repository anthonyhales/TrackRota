def is_favourite(user, rota_id: int) -> bool:
    if not user or not user.favourite_rotas:
        return False
    return rota_id in user.favourite_rotas
