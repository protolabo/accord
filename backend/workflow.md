authentification
	-> gmail-> ?
	-> outlook
		-> Have Microsoft ID ?
			-> Yes -> @router.get("/auth/{provider}/login") -> Pop up outlook auth 
											      		-> Success -> @router.get("/auth/{provider}/callback") -> Create User in database and return JWT token
													    -> Failed -> HTTP Error 
			-> Else -> @router.get("/auth/{provider}/callback") -> Skip auth and return fake token and create fake user (Shouldn't have HTTP error)
		    JWT Creation: "jwt_token = create_jwt_token({
                                                        "sub": user.user_id,
                                                        "provider": provider,
                                                        "account_id": platform_id
                                                    })
        -> Sync Emails -> @router.post("/sync_emails") -> Sync emails since a datetime -> sync and classify and save in Email database collection
        -> Generate action -> Quick action (is read) / Get date (for meeting related email) -> Return correspond result
        -> Generate thread -> Collect email class from database and group them by class -> Save in Thread collection in database
        
                                                    