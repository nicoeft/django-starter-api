# Token revocation test

### Requirements and use cases assumptions

- Multiple token per user: authentication in more than one client.
- Single token revocation: simple client logout, single token compromised.
- Multiple token revocation: logout from all devices, password change, user account compromised
- No token tracking needed: metrics like total tokens that have beeen issued/revoked/expired for a user is meaningless and have no business value.
- JWT auth library can't be changed and the solution needs to be implemented without including new dependencies.

### Implementation decisions

- Multiple token revocation:  
    This could easily be implemented with per user secret key as it's already an option in the JWT framework being used (JWT_GET_USER_SECRET_KEY setting)
    I have still decided to implement a custom per user "orig_iat" check so we can not only revoke all user's issued tokens but also do it for specific period of time (banned account).
    In both options one db access is needed either to retrieve user's secret to check jwt signature or the datetime column to be checked against jwt "orig_iat"   
    

- Single token revocation:  
    The implementation consists in a denylist for tokens. As we'll have the multi-token revocation check, this denylist will only contain the subset of tokens that are valid 
    (not expired and issued after a specific datetime) instead of all the tokens that need to be revoked, making the table faster to query.
   

- Example:  
    A user has 1000 valid tokens  issued at time=0, the user get's banned at time=2 until time=5, revocation of all these tokens requires one single row to be updated instead of 1000 inserts in a denylist.
    Then the user gets another 500 valid tokens at time=8,and after a while we decide to revoke only 10 of them, 
    we'd only insert those 10 tokens in the table and so future checks of single-token revocation will be against a 10rows table instead of 1000 (or even 1500 if all issued tokens are stored)
  
### Improvements
The DeniedToken table could be implemented with TTL option in REDIS or implement a cron task to remove denied tokens that are already expired.  
Tests of token revocation depending on a datetime should be implemented with a monkeypatch or something better than a time.sleep call.

### Other
During the test I realized JWT_ALLOW_REFRESH option was set to true but I think there were two errors regarding refreshing tokens, one was orig_iat being always setted with current time instead of reusing original token time, and the other error was also related to this, refreshing tokens in chain resulted in infinite valid tokens even though JWT_REFRESH_EXPIRATION_DELTA option was set to 7 days.
I tried to fix that and implement corresponding tests.   
Also I found that even though JWT_DECODE_HANDLER was set to use a custom method, all checks were done using the basic jwt.decode method instead.

