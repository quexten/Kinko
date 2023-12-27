# Resticat - A GTK4 & Restic based backup tool

Resticat is GTK4/Adwaita based Linux-desktop backup tool. 
As the underlying backend, restic is used. 
For now, just S3 remotes (AWS/Wasabi/Backblaze b2) are supported, but rclone and file support are planned.

When restoring, resticat automatically detects application configurations, and user files, and lets users toggle these separately.
It backups run on a schedule and triggering on other events like connecting to power, connecting to a *metered*/*unmetered* network is also possible.

## Installation
Download the flatpak from the releases page and run it.

## Screenshots
### Overview
<img src='https://github.com/quexten/resticat/assets/11866552/816aa854-4931-466c-bd66-e070c2e30f82' width='400'>

### Settings
<img src='https://github.com/quexten/resticat/assets/11866552/f46b957a-431e-4076-a0dc-e8c08703936b' width='400'>

### Restore
<img src='https://github.com/quexten/resticat/assets/11866552/8eecb912-43ea-4b00-804e-504e1a9e4f56' width='400'>
<img src='https://github.com/quexten/resticat/assets/11866552/c0aa4234-6ebf-4b57-8f85-08a7858aa91b' width='400'>

## Alternative Software
Also check out the awesome (and much more mature) Pika Backup:
https://flathub.org/apps/org.gnome.World.PikaBackup
The main advantage of Resticat is flexibility in backup targets due to restic (and rclone) support.
