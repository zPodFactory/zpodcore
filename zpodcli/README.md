# zPodFactory CLI - zpodctl

## Connection to the zPodFactory manager

`admin` is the first user auto-created on a zPodFactory manager.
It has full privileges over any operations and is considered a `superadmin`

You will need to leverage this specific user to kickstart the initial configuration for zPodFactory, or at least create another user with the same privileges level which is a special permission called `superadmin`

Every operation on the zPodFactory manager will require to be logged with a Token, without it nothing much will be possible.

Token format could look like `f"{user}_{generatedhash}"` in Python. (open to suggestions)
PS: This would provide from a quick glance which user is trying to connect, unless we want to hide that.

`zpodctl connect --server "manager.zpodfactory.io" --auth "[token]"`  
`zpodctl connect -s "manager.zpodfactory.io" -a "[token]"`  
  
PS: Will accept long & short format for `typer.Option()`  
  
## RBAC
  
zPodFactory has the ability to manage Users, Groups and Permissions.
It's a pretty common/basic model for RBAC.  
  
By default a `User` that creates a zPod will be the owner of the zPod, and will have full privileges over it.  
The owner will be automatically placed in the zPod Permission object that attaches to a Group called `owner` with the `Role` `zpod_admin`.  
  
That said `User` can be a member of one or more `Groups`, and a `Group` can have one or more `Users`.  
  
You can assign specific permissions on a zPod that will link a zPod to 1 or more `Groups` to a `Role`.
You will not be able to add a `User` directly to a zPod Permission, only a `Group`.  
Worse case you can do a `Group` with a single `User` in it if it's very specific, and assign that `Group` with a `Role` for the permission.
  
Most use cases will be:  
  
- Simple Lab setup  
  - There will probably only be a single `admin` User and everything will be done using that user. (or another user with the same privileges level)  

- MCA Lab setup
  - Only the `owner` of the zPod uses his zPod for specific/limited time use cases
  - specific(s) `Groups` will be assigned to access shared zPods (demo labs/temporary labs access, etc...)

### Users management

Here is the potential model for `User`

```python
class User(ZpodFactoryDocument):
    username: Indexed(str, unique=True) = Field(..., example="jdoe")
    email: Indexed(EmailStr, unique=True) = Field(..., example="jdoe@vmware.com")
    description: str = Field("", example="Sample User")
    api_token: Indexed(
        str,
        unique=True,
        partialFilterExpression={"api_token": {"$gt": ""}},  # noqa f722
    ) = ""
    ssh_key: str = ""
    creation_date: datetime = Field(
        default_factory=datetime.now,
        example=example_creation_date,
    )
    last_connection: datetime | None = Field(None, example=example_last_connection)
    superadmin: bool = False

    class Settings:
        name = "users"
```

Listing users:

`zpodctl users list`  

Adding a user:

`zpodctl users add --username "tsugliani" --email "timo.sugliani@gmail.com" --superadmin true`  

Editing a user:

`zpodctl users edit --username "tsugliani" --superadmin false --ssh_key "ssh-rsa AAAAB3N..."`  
`zpodctl users edit --username "tsugliani" --enabled false`  

PS: A normal `User` can only edit his `description`, `ssh_key`, and regenerate his `api_token`, evertyhing else is restricted to `superadmin`

Deleting a user:

`zpodctl users del --username "tsugliani" --confirm true`  

Some insights:  

- Only a `superadmin` can manage `Users`, `Groups` and assign `Permissions`
- A default `admin` will be created on the first boot of the zPodFactory manager with the `superadmin` permission.  

### Groups Management

Group is a simple construct with a groupname & description that will hold a list of `User`.

Listing groups:

`zpodctl groups list`

Adding a group:

`zpodctl groups add --groupname "MCA" --description "Multi-Cloud Architects"`  
`zpodctl groups add --groupname "VMware-SE-France" --description "French VCPP SEs"`  

Editing a group entitlements:

`zpodctl groups entitlements add --groupname "MCA" --username "tsugliani"`  
`zpodctl groups entitlements del --groupname "MCA" --username "tsugliani"`  

Deleting a group:

`zpodctl groups del --groupname "MCA"`  

### Permissions Management

Permissions will allow to link a zPod to a `Group` with a specific `Role` that will be applied to all the `Users` in that `Group`.

Listing permissions:

`zpodctl permissions list`  

Adding a permission:

`zpodctl permissions add --zpodname "tanzu" --groupname "MCA" --rolename "zpod_admin"`  
`zpodctl permissions add --zpodname "tanzu" --groupname "VMware-SE-France" --rolename "zpod_user"`  

Deleting a permission:

`zpodctl permissions del --zpodname "tanzu" --groupname "MCA"`  
`zpodctl permissions del --zpodname "tanzu" --groupname "VMware-SE-France"`  

## Profiles management
  
zPodFactory will provide a set of pre-defined profiles that will be available for use when deploying a zPod.  
  
You can also create your own profiles and use them when deploying a zPod. (TBD - how to create a profile)  
  
a zPod Profile is a JSON file representing the components that will be orderly deployed in a zPod.  
  
Listing profiles:  
  
`zpodctl profiles list`  
`zpodctl profiles update` // (will very likely update from github repo with latest profiles `git pull`)  

Getting info on a specific profile:  
  
`zpodctl profiles info --profilename "sddc-basic-7.0u3i"` // will display the components in order  
`zpodctl profiles info -p "sddc-basic-7.0u3i"`  
  
Getting status of a specific profile:  
  
`zpodctl profiles status --profilename "sddc-basic-7.0u3i"` // will display the components in order with their status (available, not available)  
  
For a profile to be available, all the components it contains must be available in the zPodFactory Library.
PS: Remember that without binaries of the various components, zPodFactory will not be able to deploy them, so we will have scheduled task & zpodctl command to verify/resync the status.
  
`zpodctl profile status --rescan/verify`  

## Components management

zPodFactory will provide a list of components for most of the VMware products that can be deployed on a zPod. (vcsa, esxi, nsx, hcx, vcd, vrops, vrli, etc...)

It will also provide some specific non VMware components that are necessary for the zPod to function normally such as:  
  
- zBox VM (a mandatory utility vm with some important features)  
  - Provides NFS Datastore for the zPod  
  - Provides DNS/DHCP/NTP/SSH/WireGuard Access for the zPod Layer 2 main network  
  
- VyOS VM ([https://vyos.io](https://vyos.io))
  - Provides some networking features with a known Network CLI for most network engineers/admins (that don't like doing this on a linux vm such as zBox)  
  - Can provide VLAN/BGP features  
  - Might be used for some other features that are currently covered by the zBox today  

Listing components:  
  
`zpodctl components list`  
  
Updating components:  
  
`zpodctl components update` // (will very likely update from github repo with latest components `git pull`)  
  
Getting info on a specific component:  
  
`zpodctl components info --componentname "vcsa-7.0u3i"` // will display the components JSON data.  
  
For now I'll not put commands to create/update/delete components, but we can discuss it later when we need it.  
This shouldn't be a big problem anyway as the structure is pretty detailed now for the zpodlibrary/components etc...  


## Library management

TBD

`zpod libraries list`



## Endpoints management

`zpodctl endpoints list`

`zpodctl endpoints add --endpointname "RAX-MCA"`

`zpodctl endpoints compute add --endpointname "RAX-MCA" --server "vc01.rax.lab" --username "zpod_svc@vmc.lab" --password "XXYYZZ"`
`zpodctl endpoints storage add --endpointname "RAX-MCA" --datastore "vSanDatastore"`


`zpodctl endpoints network xyz` // NOW THIS IS THE COMPLEX PART :D

`zpodctl endpoints network add --endpointname "RAX-MCA" --driver "NSXT+VyOS" --nsxt_manager "nsx01.rax.lab" --nsxt_username "admin" --nsxt_password "XXYYZZ"`


`zpodctl endpoints network add --endpointname "HomeLab" --driver "VyOS"`

`zpodctl endpoints validate --endpointname "RAX-MCA"`
`zpodctl endpoints validate --endpointname "Homelab"`

## zPod management

`zpodctl pod list`
`zpodctl pod info --name "tanzeu"`

`zpodctl pod deploy --name "tanzu" --profilename "sddc-basic-7.0u3i" --endpoint "rax-mca"`
`zpodctl pod deploy -n "tanzu" -p "sddc-basic-7.0u3i" -e "rax-mca"`


`zpodctl pod permissions add --zpodname "tanzu" --groupname "MCA" --rolename "zpod_admin"`
`zpodctl pod permissions add --zpodname "tanzu" --groupname "VMware-SE-France" --rolename "zpod_user"`
