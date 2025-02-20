##############################################################################
# Copyright 2025 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

'''Test data'''

SPEC_COMMANDS_SVC_SIMPLE = r'''
<Commands>
    <Executable name="svcinfo">
        <Command name="catauditlog">
            <Response type="svc_normal" param=""/>
            <ValueParam name="-first"/>
            <ValueParam name="-delim"/>
        </Command>
    </Executable>
    <Executable name="svctask">
        <Command name="detectmdisk">
            <Response type="svc_status" param=""/>
        </Command>
    </Executable>
    <Executable name="sainfo">
        <Command name="lsfiles">
            <Response type="svc_concise" param=""/>
            <ValueParam name="-panel_name" noName="true"/>
            <ValueParam name="-prefix"/>
        </Command>
    </Executable>
    <Executable name="satask">
        <Command name="chwwnn">
            <Response type="svc_status" param=""/>
            <ValueParam name="-panel_name" noName="true"/>
            <FlagParam name="-wwnnsuffix"/>
        </Command>
    </Executable>
</Commands>
        '''

SPEC_BAD_XML_PI = r'''
<?xml version="1.0" encoding="UTF-8"?>
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>

'''
SPEC_NO_VERSION = r'''
<ArraySyntax>
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_NO_ARRAY_TYPE = r'''
<ArraySyntax version="2.0">
    <ArrayType><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_NO_ERROR = r'''
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error> </Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_NO_EXE_NAME = r'''
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable>
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_EMPTY_EXE_NAME = r'''
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name=" ">
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_NO_CMD_NAME = r'''
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command>
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
            <Command name='lscluster'>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_EMPTY_CMD_NAME = r'''
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command name="">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam name="-delim"/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_NO_PARAM_NAME = r'''
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ValueParam/>
                <FlagParam name="-filtervalue?"/>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

SPEC_EMPTY_PARAM_NAME = r'''
<ArraySyntax version="2.0">
    <ArrayType type="svc"><ArrayVersion type="svc" version="6.3"/></ArrayType>
    <Errors><Error>CMMV</Error></Errors>
    <Commands>
        <Executable name="svcinfo">
            <Command name="lscluster">
                <Response type="svc_normal"/>
                <ValueParam name="-filtervalue"/>
                <FlagParam name="-nohdr"/>
                <FlagParam name="-bytes"/>
                <ParamChoice>
                <ValueParam name="-delim"/>
                <FlagParam name=" "/>
                </ParamChoice>
                <ValueParam name="cluster_id_or_name" noName="true"/>
            </Command>
        </Executable>
    </Commands>
</ArraySyntax>
'''

RESP_svcinfo_nothing = r''

RESP_svcinfo_lscluster = r'''
id,name,location,partnership,bandwidth,id_alias
000002006700D9FC,CIMV7000,local,,,000002006700D9FC
000002006500C4FC,CIMFVTV7000,remote,fully_configured,20,000002006500C4FC
'''

RESP_svcinfo_lscluster_id = r'''
id,000002006700D9FC
name,CIMV7000
location,local
partnership,
bandwidth,
total_mdisk_capacity,2.3TB
space_in_mdisk_grps,2.2TB
space_allocated_to_vdisks,246.81GB
total_free_space,2.0TB
statistics_status,on
statistics_frequency,15
required_memory,0
cluster_locale,en_US
time_zone,522 UTC
code_level,6.3.0.0 (build 52.5.1106290000)
FC_port_speed,2Gb
console_IP,9.119.41.132:443
id_alias,000002006700D9FC
gm_link_tolerance,300
gm_inter_cluster_delay_simulation,0
gm_intra_cluster_delay_simulation,0
email_reply,
email_contact,
email_contact_primary,
email_contact_alternate,
email_contact_location,
email_state,stopped
inventory_mail_interval,0
total_vdiskcopy_capacity,251.62GB
total_used_capacity,241.68GB
total_overallocation,10
total_vdisk_capacity,251.62GB
cluster_ntp_IP_address,
cluster_isns_IP_address,
iscsi_auth_method,none
iscsi_chap_secret,
auth_service_configured,no
auth_service_enabled,no
auth_service_url,
auth_service_user_name,
auth_service_pwd_set,no
auth_service_cert_set,no
relationship_bandwidth_limit,25
gm_max_host_delay,5
tier,generic_ssd
tier_capacity,0.00MB
tier_free_capacity,0.00MB
tier,generic_hdd
tier_capacity,2.20TB
tier_free_capacity,1.95TB
email_contact2,
email_contact2_primary,
email_contact2_alternate,
total_allocated_extent_capacity,247.03GB
has_nas_key,no
auth_service_type,tip
layer,controller
'''

RESP_svcinfo_lsvdisk = r'''
id,name,IO_group_id,IO_group_name,status,mdisk_grp_id,mdisk_grp_name,capacity,type,FC_id,FC_name,RC_id,RC_name,vdisk_UID,fc_map_count,copy_count,fast_write_state,se_copy_count,compressed_copy_count
0,vdisk0,0,io_grp0,online,5,mdiskgrp2,100.00MB,striped,0,fcmap0,0,rcrel8,60050768019C0367F000000000000023,1,1,empty,0,0
1,vdisk1,0,io_grp0,offline,5,mdiskgrp2,100.00MB,striped,0,fcmap0,0,rcrel8,60050768019C0367F000000000000024,1,1,empty,0,0
2,vc_plugin_volume1,0,io_grp0,online,4,forvcplugintest,40.00GB,striped,,,,,60050768019C0367F000000000000025,0,1,empty,0,0
3,vc_plugin_volume2,0,io_grp0,online,4,forvcplugintest,40.00GB,striped,,,,,60050768019C0367F000000000000026,0,1,empty,0,0
'''

RESP_svcinfo_lsvdisk_id = r'''
id,0
name,vdisk0
IO_group_id,0
IO_group_name,io_grp0
status,online
mdisk_grp_id,5
mdisk_grp_name,mdiskgrp2
capacity,100.00MB
type,striped
formatted,no
mdisk_id,
mdisk_name,
FC_id,0
FC_name,fcmap0
RC_id,0
RC_name,rcrel8
vdisk_UID,60050768019C0367F000000000000023
throttling,0
preferred_node_id,2
fast_write_state,empty
cache,readwrite
udid,
fc_map_count,1
sync_rate,50
copy_count,1
se_copy_count,0
filesystem,
compressed_copy_count,0

copy_id,0
status,online
sync,yes
primary,yes
mdisk_grp_id,5
mdisk_grp_name,mdiskgrp2
type,striped
mdisk_id,
mdisk_name,
fast_write_state,empty
used_capacity,100.00MB
real_capacity,100.00MB
free_capacity,0.00MB
overallocation,100
autoexpand,
warning,
grainsize,
se_copy,no
easy_tier,on
easy_tier_status,inactive
tier,generic_ssd
tier_capacity,0.00MB
tier,generic_hdd
tier_capacity,100.00MB
compressed_copy,no
'''

RESP_svcinfo_lssevdiskcopy = r'''
vdisk_id,vdisk_name,copy_id,mdisk_grp_id,mdisk_grp_name,capacity,used_capacity,real_capacity,free_capacity,overallocation,autoexpand,warning,grainsize,se_copy,compressed_copy
13,wayneTest12,0,0,waynestudy720,1.00GB,0.41MB,528.38MB,527.97MB,193,on,0,32,yes,no
14,waynetest13,0,0,waynestudy720,1.00GB,0.41MB,528.38MB,527.97MB,193,on,0,32,yes,no
15,vdisk3,0,0,waynestudy720,1.00GB,0.41MB,528.38MB,527.97MB,193,on,80,32,yes,no
16,waynetest14,0,0,waynestudy720,1000.00MB,0.41MB,516.38MB,515.97MB,193,on,80,32,yes,no
17,waynetest15,0,0,waynestudy720,1000.00MB,0.75MB,516.50MB,515.75MB,193,on,80,256,yes,no
28,vdisk4,0,0,waynestudy720,1.00GB,0.75MB,528.50MB,527.75MB,193,on,80,256,yes,no
31,vdisk5,0,7,waynetest1,1.00GB,0.41MB,528.38MB,527.97MB,193,on,80,32,yes,no
32,grainsizetest,0,7,waynetest1,1.00GB,0.41MB,528.38MB,527.97MB,193,on,80,32,yes,no
33,grainsizetest1,0,7,waynetest1,1.00GB,0.41MB,528.38MB,527.97MB,193,on,80,32,yes,no
34,grainsizetest2,0,7,waynetest1,1.00GB,0.41MB,528.38MB,527.97MB,193,on,80,32,yes,no
35,waynetest25,0,0,waynestudy720,1000.00MB,0.75MB,516.50MB,515.75MB,193,on,80,256,yes,no
'''

RESP_svcinfo_lssevdiskcopy_id = r'''
vdisk_id,vdisk_name,copy_id,mdisk_grp_id,mdisk_grp_name,capacity,used_capacity,real_capacity,free_capacity,overallocation,autoexpand,warning,grainsize,se_copy,compressed_copy
15,vdisk3,0,0,waynestudy720,1.00GB,0.41MB,528.38MB,527.97MB,193,on,80,32,yes,no
'''

# e.g. "svcinfo lssevdiskcopy -delim , -copy 0 15"
RESP_svcinfo_lssevdiskcopy_id_copy = r'''
vdisk_id,15
vdisk_name,vdisk3
capacity,1.00GB
copy_id,0
status,online
sync,yes
primary,yes
mdisk_grp_id,0
mdisk_grp_name,waynestudy720
type,striped
mdisk_id,
mdisk_name,
fast_write_state,empty
used_capacity,0.41MB
real_capacity,528.38MB
free_capacity,527.97MB
overallocation,193
autoexpand,on
warning,80
grainsize,32
se_copy,yes
easy_tier,on
easy_tier_status,inactive
tier,generic_ssd
tier_capacity,0.00MB
tier,generic_hdd
tier_capacity,528.38MB
compressed_copy,no
'''

RESP_svcinfo_lsclusterip = r'''
cluster_id,cluster_name,location,port_id,IP_address,subnet_mask,gateway,IP_address_6,prefix_6,gateway_6
000002006700D9FC,CIMV7000,local,1,9.119.41.132,255.255.255.0,9.119.41.1,,,
000002006700D9FC,CIMV7000,local,2,,,,,,
000002006500C4FC,CIMFVTV7000,remote,1,9.119.41.113,255.255.255.0,9.119.41.1,,,
000002006500C4FC,CIMFVTV7000,remote,2,,,,,,
'''

RESP_svcinfo_lsclusterip_id = r'''
cluster_id,000002006700D9FC
cluster_name,CIMV7000
location,local
port_id,1
IP_address,9.119.41.132
subnet_mask,255.255.255.0
gateway,9.119.41.1
IP_address_6,
gateway_6,
prefix_6,

cluster_id,000002006700D9FC
cluster_name,CIMV7000
location,local
port_id,2
IP_address,
subnet_mask,
gateway,
IP_address_6,
gateway_6,
prefix_6,
'''

RESP_svcinfo_lscurrentuser = r'''
name,superuser
role,SecurityAdmin
'''

RESP_svcinfo_lshbaportcandidate = r'''id
50050768014043E4
5005076802301806
500507680140436C'''

RESP_svcinfo_lssoftwareupgradestatus = r'''
status 
inactive 
'''

RESP_svcinfo_lsroute = r'''
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
9.119.41.0      0.0.0.0         255.255.255.0   U     0      0        0 eth0
127.0.0.0       0.0.0.0         255.0.0.0       U     0      0        0 lo
0.0.0.0         9.119.41.1      0.0.0.0         UG    0      0        0 eth0


Kernel IPv6 routing table
Destination                                 Next Hop                                Flags Metric Ref    Use Iface
fe80::/64                                   ::                                      U     256    0        0 eth0    
::1/128                                     ::                                      U     0      4223      18 lo      
fe80::e61f:13ff:fe74:61f/128                ::                                      U     0      0        1 lo      
ff00::/8                                    ::                                      U     256    0        0 eth0    
'''

RESP_svcinfo_lsnodevpd_id = r'''
id,1

system board: 23 fields
part_number,85Y5899
system_serial_number,RCK0949138G004D
number_of_processors,1
number_of_memory_modules,2
number_of_fans,2
number_of_generic_devices,2
number_of_FC_adapters,1
number_of_Ethernet_adapters,2
number_of_SAS_adapters,1
number_of_Bus_adapters,1
number_of_power_supplies,2
number_of_local_managed_disks,0
BIOS_manufacturer,American Megatrends Inc.
BIOS_version,124
BIOS_release_date,03/25/2011
system_manufacturer,Xyratex
system_product,Storage Server
planar_manufacturer,Xyratex                          
CMOS_battery_part_number,TB CMOS
frame_assembly_part_number,TB FRAME
power_cable_assembly_part_number,TB PWRCBL
service_processor_firmware,332
disk_controller,TB SAS CARD

processor: 6 fields
part_number,TB PROC
processor_location,Processor 1
manufacturer,Intel            
version,Intel(R) Xeon(R) CPU C3539 @ 2.13GHz           
speed,2128
status,Enabled

memory module: 12 fields
part_number,TB MEMORY
device_location,CHA DIMM0
bank_location,BANK0
size (MB),4096
manufacturer,Undefined       
serial_number,423C15CF  

part_number,TB MEMORY
device_location,CHB DIMM0
bank_location,BANK0
size (MB),4096
manufacturer,Undefined       
serial_number,423C1615  

fan: 4 fields
part_number,TB FAN
location,location1

part_number,TB FAN
location,location2

Adapter card: 9 fields
card_type,FC
part_number,85Y5899
port_numbers,1 2 3 4
location,0
device_serial_number,BLANK
manufacturer,IBM
device,QE8 Fibre Channel Host Adapter
card_revision,0
chip_revision,2.0

Fibre channel SFP: 48 fields
part_number,31P1338
manufacturer,JDSU
device,PLRXPLVCSH423N
serial_number,C952VK178
supported_speeds,2,4,8
connector_type,LC
transmitter_type,SN
wavelength,850
max_distance_by_cable_type,OM1:20,OM2:50,OM3:150
hw_revision,2
port_number,1
WWPN,5005076801106d3e

part_number,31P1338
manufacturer,JDSU
device,PLRXPLVCSH423N
serial_number,C952VK170
supported_speeds,2,4,8
connector_type,LC
transmitter_type,SN
wavelength,850
max_distance_by_cable_type,OM1:20,OM2:50,OM3:150
hw_revision,2
port_number,2
WWPN,5005076801206d3e

part_number,31P1338
manufacturer,JDSU
device,PLRXPLVCSH423N
serial_number,C940VK03Q
supported_speeds,2,4,8
connector_type,LC
transmitter_type,SN
wavelength,850
max_distance_by_cable_type,OM1:20,OM2:50,OM3:150
hw_revision,1
port_number,3
WWPN,5005076801306d3e

part_number,31P1338
manufacturer,JDSU
device,PLRXPLVCSH423N
serial_number,C935VK05E
supported_speeds,2,4,8
connector_type,LC
transmitter_type,SN
wavelength,850
max_distance_by_cable_type,OM1:20,OM2:50,OM3:150
hw_revision,1
port_number,4
WWPN,5005076801406d3e

Adapter card: 36 fields
card_type,Ethernet
part_number,85Y5899
port_numbers,1
location,0
device_serial_number,Unknown
manufacturer,Unknown
device,Intel (R)82574L Gigabit Ethernet Controller
card_revision,Unknown
chip_revision,0.0

card_type,Ethernet
part_number,85Y5899
port_numbers,2
location,0
device_serial_number,Unknown
manufacturer,Unknown
device,Intel (R)82574L Gigabit Ethernet Controller
card_revision,Unknown
chip_revision,0.0

card_type,SAS
part_number,85Y5899
port_numbers,1 2
location,0
device_serial_number,Unknown
manufacturer,Unknown
device,PMC Sierra 6G SAS/SATA Controller
card_revision,Unknown
chip_revision,1.1

card_type,Bus
part_number,85Y5899
port_numbers,1
location,0
device_serial_number,Unknown
manufacturer,Unknown
device,48 lane PCI Express GEN 2 Switch
card_revision,Unknown
chip_revision,46.3

device: 16 fields
part_number,TB N/A
bus,TB N/A
device,0
model,
revision,
serial_number,
approx_capacity,0
hw_revision,0

part_number,85Y5899
bus,sata
device,0
model,SanDisk pSSD-S2 32GB
revision,SSD 6.30
serial_number,102146300072
approx_capacity,29
hw_revision,

software: 4 fields
id,1
node_name,node1
WWNN,0x5005076801006d3e
code_level,6.3.0.0 (build 52.5.1106290000)

front panel assembly: 3 fields
part_number,TB N/A
front_panel_id,01-2
dump_name,32G00SG-2

ethernet port: 8 fields
port_number,1
ethernet_status,1
MAC_address,e4:1f:13:74:06:1f
supported_speeds,10/100/1000

port_number,2
ethernet_status,0
MAC_address,e4:1f:13:74:06:1e
supported_speeds,10/100/1000
'''

# e.g. "svctask mkvdisk -iogrp 0 -mdiskgrp 1 -size 100 -unit mb"
RESP_svctask_mkvdisk = r'''
Virtual Disk, id [36], successfully created
'''

# e.g " svctask mkvdisk -iogrp 0 -mdiskgrp 1 -size 100 -unit mb -nomsg"
RESP_svctask_mkvdisk_nomsg = r'''
36
'''

RESP_svctask_mkvdisk_err = r'''CMMVC6432E The command failed because the specified managed disk group does not exist.'''
