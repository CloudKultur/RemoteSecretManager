# Setup
Download the proper version from the Packages section and copy them into your `/usr/local/bin` directory.

After starting you will be prompted for your Gitlab token, which will be stored in a `.env` file (see `.env.template`) in your home path `~/.gcm/.env`:
```
TOKEN=<token>
```

The database will also be stored in that directory.
# Usage
In the directory where you want to use tok, ensure you created a `.env` file with your Gitlab token, then you can use this tool:

`python3 main.py --help`

- use `--pull` to fetch your projects
- use `--projects` to show you projects and id's
- use `--select 12345678` to select your project by id and fetch the keys
- use `--rm` to delete your database
- use `--keys` to update the keys for your selected project
- use `--print` to write the keys with values to stdout
- use `--env` to filter by envronment
- use `use -- <mycommand --foo bar>` to pass the variables to your command
    - use `--env <environment>` before to filter environment variables based on the environment, for example `use --env Development use -- <mycommand>`
- use `set VariableName Value` to create a variable
    - `--raw` or `-r` for raw string
    - `--masked` or `-m` for masked (value >= 8 characters needed)
    - `--protected` or `-p` for protected
    - `--env <environment>` or `-e <environment>` for environment selection

For your daily use, you probably want to `--pull` all of your projects. 
Then you would want to list all of your `--projects` to look for your desired 
projects id. After getting the id, you can `--select 12345678` your project by id.
You can now start using your tool with the projects environments variables using 
`use -- mycommand --foo bar`

You can select variables by environment using `--env <environment>`. For example using `--env development use mycommand --foo bar`. 

## Credential Encryption
The Credentials are encrypted using [Python Cryptography](https://cryptography.io/en/latest/)
with symmetric AES in CBC mode with a 128-bit key (PKCS7) for encryption and provides 
HMAC using SHA256 for authentication. The implementation is Fernet.

The key is the SHA256-Hash of the gitlab-token and results in an 32 byte value for Fernet.

# Development
- install python
- `pip3 install -r requirements.txt`

# Building
Use `pyinstaller`, install via `pip3 install pyinstaller`.

You can adjust the target architecture by setting it to `x86_64` or `arm64` for a mac.
Then execute:

`pyinstaller -F --target-arch x86_64 -n gcm main.py`

## WIP: Building with docker
Run locally:
- `docker build -t gitlabcredentialsmanager:latest .`
- `docker run -it --volume "./:/app"  --rm gitlabcredentialsmanager:latest`
- `gcm` can be found in directory `./dist`