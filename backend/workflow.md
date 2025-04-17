authentification
	-> gmail-> ?
	-> outlook
		-> Have Microsoft ID ?
			-> Yes -> @router.get("/outlook/login") -> Pop up outlook auth 
											      		-> Success -> @router.get("/outlook/callback") -> Return true token and user
													-> Failed -> HTTP Error 
			-> Else -> @router.get("/outlook/callback") -> Skip auth and return fake token and user (Shouldn't have HTTP error)
		-> Create JWT -> "jwt_token": create_jwt_token({"sub": user.google_id / user.microsoft_id, "platform": user.platform})
    