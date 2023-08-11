# scraper-clients
This contains all current scraper clients

## Config
Because this repository has multiple individual programs, I dont use a .env for environment variables, instead I use a `config.json` file in the root directory. To set this file up, create
it and then fill in the file with the fields below:

```json
{
    // your scraper username
    "username": "joeys123",
    // your scraper password
    "password": "joe_smoove",
    // leave username and password like this, do not insert your value
    "proxy_url": "socks5://{username}:{password}@13.253.142.52:1080",
    // username for proxy
    "proxy_username": "my_proxy_username",
    // password for proxy
    "proxy_password": "my_proxy_password"
}
```

