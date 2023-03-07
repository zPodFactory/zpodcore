# zPodFactory CLI - zpodctl

## Connection to the zPodFactory manager

`admin` is the first user auto-created on a zPodFactory manager.
It has full privileges over any operations and is considered a `superadmin`

You will need to leverage this specific user to kickstart the initial configuration for zPodFactory, or at least create another user with the same privileges level which is a special permission called `superadmin`

Every operation on the zPodFactory manager will require to be logged with a Token, without it nothing much will be possible.

Token format could look like `f"{user}_{generatedhash}"` in Python. (open to suggestions)
PS: This would provide from a quick glance which user is trying to connect, unless we want to hide that.

`zcli connect --server "manager.zpodfactory.io" --token "[token]"`  
`zcli connect -s "manager.zpodfactory.io" -t "[token]"`  
  
PS: Will accept long & short format for `typer.Option()`  

## zPodFactory instance settings

We will very likely have a new command to setup some instance wide settings for zPodFactory that can only be altered by a `superadmin`:

## Customer Connect Download facility

Setting customer connect credentials for automatic downloads:

`zcli settings customerconnect -u "timo.sugliani@gmail.com" -p "amazingpassword"`

## zPodFactory main DNS domain for zPods

Setting the main domain name for zPodfactory that will be leverage for every deployed zPod:

`zcli settings domain -s "cool.zpod.io"`

This will make that every zpod deployed will inherit the default domain name and add the name as the subdomain of this main domain.

Example: zPod name = tanzu
Subdomain for the whole zPod will be `tanzu.cool.zpod.io` and sample hostnames will be:

- `zbox.tanzu.cool.zpod.io`
- `esx11.tanzu.cool.zpod.io`
- `esx12.tanzu.cool.zpod.io`
- `vcsa.tanzu.cool.zpod.io`
- `nsxt.tanzu.cool.zpod.io`


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

`zcli user list`  

Adding a user:

`zcli user add --username "tsugliani" --email "tsugliani@vmware.com" --superadmin true`  

Editing a user:

`zcli user edit --username "tsugliani" --superadmin false --ssh_key "ssh-rsa AAAAB3N..."`  
`zcli user edit --username "tsugliani" --enabled false`  

PS: A normal `User` can only edit his `description`, `ssh_key`, and regenerate his `api_token`, evertyhing else is restricted to `superadmin`

Deleting a user:

`zcli user del --username "tsugliani" --confirm true`  

Some insights:  

- Only a `superadmin` can manage `Users`, `Groups` and assign `Permissions`
- A default `admin` will be created on the first boot of the zPodFactory manager with the `superadmin` permission.  

### Groups Management

Group is a simple construct with a groupname & description that will hold a list of `User`.

Listing groups:

`zcli group list`

Adding a group:

`zcli group add --groupname "MCA" --description "Multi-Cloud Architects"`  
`zcli group add --groupname "VMware-SE-France" --description "French VCPP SEs"`  

Editing a group entitlements:

`zcli group entitlements add --groupname "MCA" --username "tsugliani"`  
`zcli group entitlements del --groupname "MCA" --username "tsugliani"`  

Deleting a group:

`zcli group del --groupname "MCA"`  

### Permissions Management

Permissions will allow to link a zPod to a `Group` with a specific `Role` that will be applied to all the `Users` in that `Group`.

Listing permissions:

`zpodctl permission list`  

Adding a permission:

`zpodctl permission add --zpodname "tanzu" --groupname "MCA" --rolename "zpod_admin"`  
`zpodctl permission add --zpodname "tanzu" --groupname "VMware-SE-France" --rolename "zpod_user"`  

Deleting a permission:

`zpodctl permission del --zpodname "tanzu" --groupname "MCA"`  
`zpodctl permission del --zpodname "tanzu" --groupname "VMware-SE-France"`  

## Profiles management
  
zPodFactory will provide a set of pre-defined profiles that will be available for use when deploying a zPod.  
  
You can also create your own profiles and use them when deploying a zPod. (TODO: How to create a profile)  
  
a zPod Profile might be a python wrapper/template type file representing the components that will be orderly deployed in a zPod with the dependency chain & component name/versions.
Hopefully this will provide a very simple way to leverage prefect capabilities, but also having safeguards to verify that the information we setup in those profiles is still valid and can be deployed.
  
Listing profiles:  
  
`zcli profile list`  
`zcli profile update` // (will very likely update from github repo with latest profiles `git pull`)  
TODO: similar process to libraries, will the library contain the profiles too, that could make sense ?

Getting info on a specific profile:  
  
`zcli profile info --profilename "sddc-basic-7.0u3i"` // will display the components in order  
`zcli profile info -p "sddc-basic-7.0u3i"`  
  
Getting status of a specific profile:  
  
`zcli profile status --profilename "sddc-basic-7.0u3i"` // will display the components in order with their status (available, not available)  
  
For a profile to be available, all the components it contains must be available in the zPodFactory Library.
PS: Remember that without binaries of the various components, zPodFactory will not be able to deploy them, so we will have scheduled task & zpodctl command to verify/resync the status.
  
`zcli profile status --rescan/verify`  

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
  
`zcli component list`  
  
Getting info on a specific component:  
  
`zcli component info --componentname "vcsa-7.0u3i"` // will display the components JSON data.  
  
For now I'll not put commands to create/update/delete components, but we can discuss it later when we need it.  
This shouldn't be a big problem anyway as the structure is pretty detailed now for the zpodlibrary/components etc...  

`zcli component enable -c|--componentname "vcsa-7.0u3i"`

When a component is `enabled` this will automatically trigger the zPodFactory download engine for the specified component.

Actually it can manage 2 different download engines:
- `customerconnect`: This will leverage the `vcc` with specific customer connect credentials (obviously you will need to be entitled to the components you expect to use/download as those products are licensed by VMware)
- `https`: This will leverage a tradition https public link, that can be shared without any constraints.

This will greatly improve the UX for the users of this lab platform, as managing / maintaining the lifecycle of all products & versions deployed. 


## Scripts management

`zcli script list`

## Library management

Library is the main object that hosts all components managed by zPodFactory

By default the main library for zPod will be auto-added: https://github.com/zPodFactory/zPodLibrary

Listing libraries:

`zcli library list`

Adding Library:

`zcli library add --name "main" --git_url "https://github.com/zPodFactory/zPodLibrary"`

Updating library:  
  
`zcli library update` // (will very likely update from github repo with latest components `git pull`)  

This will update the list of components based on that git repository & update/add all the new components that may have been added since.

TODO: Scheduled task to update automatically this library & it's components to enhance the UX.


## Endpoints management

Endpoints will be use to specify the deployment target for a zPod, and be a combination of vSphere resources, networking etc.

Listing endpoints:

`zcli endpoint list`

Adding endpoint:

`zcli endpoint add --endpointname "RAX-MCA" --json @endpoint.json`

The `endpoint.json` file would look something like this:

```json
{
  "compute":
  {
    "name": "my-vsphere-endpoint",
    "driver": "vsphere",
    "hostname": "my-vcenter.com",
    "username": "my-username",
    "password": "my-password",
    "datacenter": "my-datacenter",
    "resource_pool": "my-cluster",
    "storage_policy": "my-storage-policy",
    "storage_datastore": "my-datastore",
    "contentlibrary": "my-contentlibrary",
    "vmfolder": "my-vmfolder"
  },
  "network":
  {
    "name": "my-network-endpoint",
    "driver": "nsxt",
    "hostname": "my-nsxt-manager.com",
    "username": "my-username",
    "password": "my-password",
    "transportzone": "my-transportzone",
    "edgecluster": "my-edgecluster",
    "t0": "my-t0"
  }
}
```

Validating an endpoint:

`zcli endpoint validate --endpointname "RAX-MCA"`

`zcli endpoint validate --endpointname "Homelab"`

This command will ensure the endpoint is valid, and will set it's `enabled` property (boolean) to `true`

## zPod management

`zcli pod list`

`zcli pod info --name "tanzu"`

`zcli pod deploy --name "tanzu" --profilename "sddc-basic-7.0u3i" --endpoint "rax-mca"`

`zcli pod deploy -n "tanzu" -p "sddc-basic-7.0u3i" -e "rax-mca"`

`zcli pod permissions add --zpodname "tanzu" --groupname "MCA" --rolename "zpod_admin"`

`zcli pod permissions add --zpodname "tanzu" --groupname "VMware-SE-France" --rolename "zpod_user"`
