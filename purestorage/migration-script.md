## Python FileSystem Migration Script

### Goals
- GET/Query flashblade filesystems information
    - names
    - nfs / smb rules and policies
    - provisioned size
    - virtual size
    - etc...

- POST/Create a new filesystem with proper configurations if neccessary
    - name
    - provision size
    - nfs / smb
    - rules / policy
    - hard limit
    - writable
    - etc

- PATCH/Update an existing filesystem with new or additional configurations
    - Destroyed
    - provisioned size
    - rules / policy
    - hard limit
    - writable
    - etc

- DELETE/Remove an existing filesystem
    - destroyed : True
    - Filesystem must be "destroyed", and only then can it be fully "eradicated" from API.
    - NOTE: Always verify before deleting filesystems.
