# Authentication Setup

This directory contains the `.htpasswd` file for Nginx basic authentication.

## Creating the .htpasswd file

To create user credentials for accessing the application:

### First user:
```bash
htpasswd -c .htpasswd username1
```

### Additional users:
```bash
htpasswd .htpasswd username2
htpasswd .htpasswd username3
```

## Important Notes

- The `-c` flag creates a new file. Only use it for the first user.
- For additional users, omit the `-c` flag to append to the existing file.
- Choose strong passwords for production use.
- The `.htpasswd` file should not be committed to version control.
- Keep a secure backup of usernames and passwords.

## Example

```bash
# Create first user
htpasswd -c .htpasswd admin

# Add team members
htpasswd .htpasswd developer1
htpasswd .htpasswd developer2
htpasswd .htpasswd viewer
```

## Security

- This file contains hashed passwords but should still be kept secure.
- Set appropriate file permissions: `chmod 644 .htpasswd`
- The file is mounted into the Nginx container via docker-compose.yml