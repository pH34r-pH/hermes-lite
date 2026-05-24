"""SystemdClient — wrapper for systemctl commands on the VM.

Supports status query, restart, and bounded journalctl reading
via ssh or az-vm-run-command.
"""

__version__ = "1.0.0"
