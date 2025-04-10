"""Build recipe for the ISC Bind 9 container image."""

from pathlib import Path

from bci_build.container_attributes import NetworkPort
from bci_build.container_attributes import NetworkProtocol
from bci_build.os_version import ALL_NONBASE_OS_VERSIONS
from bci_build.os_version import CAN_BE_LATEST_OS_VERSION
from bci_build.package import DOCKERFILE_RUN
from bci_build.package import ApplicationStackContainer
from bci_build.package import ParseVersion
from bci_build.package import Replacement

_BIND_FILES = {
    "entrypoint.sh": (
        (_bind_dir := Path(__file__).parent / "bind") / "entrypoint.sh"
    ).read_text(),
    "healthcheck.sh": (_bind_dir / "healthcheck.sh").read_text(),
}

BIND_CONTAINERS = [
    ApplicationStackContainer(
        name="bind",
        os_version=os_version,
        is_latest=os_version in CAN_BE_LATEST_OS_VERSION,
        version=9,
        pretty_name="ISC BIND 9",
        version_in_uid=False,
        package_list=["bind"],
        exposes_ports=[
            NetworkPort(53),
            NetworkPort(53, NetworkProtocol.UDP),
            NetworkPort(953),
            NetworkPort(853),
            NetworkPort(443),
        ],
        additional_versions=[
            (_bind_minor_re := "%%bind_major_minor%%"),
            (_bind_patch_re := "%%bind_major_minor_patch%%"),
        ],
        replacements_via_service=[
            Replacement(_bind_minor_re, "bind", parse_version=ParseVersion.MINOR),
            Replacement(_bind_patch_re, "bind", parse_version=ParseVersion.PATCH),
        ],
        extra_files=_BIND_FILES,
        env={
            # copy-pasta from /etc/sysconfig/named
            "RNDC_KEYSIZE": 512,
            "NAMED_ARGS": "",
            "NAMED_INITIALIZE_SCRIPTS": "",
            # need to set this one so that we can override it
            "NAMED_CONF": "/etc/named.conf",
        },
        custom_end=rf"""COPY entrypoint.sh {(_entrypoint := "/usr/local/bin/entrypoint.sh")}
COPY healthcheck.sh {(_healthcheck := "/usr/local/bin/healthcheck.sh")}
{DOCKERFILE_RUN} \
    chmod +x {_entrypoint}; \
    chmod +x {_healthcheck};

# patch named.prep to not call logger (provided by systemd)
# and just log to stdout
{DOCKERFILE_RUN} \
    mkdir -p /usr/local/lib/bind; \
    cp {os_version.libexecdir}bind/named.prep {(_named_prep := "/usr/local/lib/bind/named.prep")}; \
    sed -i -e 's|logger "Warning: \$1"|echo "Warning: \$1" >\&2|' -e '/\. \$SYSCONFIG_FILE/d' {_named_prep}

# create directories that tmpfiles.d would create for us
{DOCKERFILE_RUN} \
"""
        + (r" \ " + "\n").join(
            (
                f"    mkdir -p {dirname}; chown {user} {dirname}; chmod {mode} {dirname};"
                for dirname, mode, user in (
                    ("/run/named", "1775", "root:named"),
                    ("/var/lib/named", "1775", "root:named"),
                    ("/var/lib/named/dyn", "755", "named:named"),
                    (
                        "/var/lib/named/master",
                        "755",
                        "root:root" if os_version.is_tumbleweed else "named:named",
                    ),
                    ("/var/lib/named/slave", "755", "named:named"),
                    ("/var/log/named", "750", "named:named"),
                )
            )
        )
        + f"""
# create files that tmpfiles.d would create for us
{DOCKERFILE_RUN} touch /var/lib/named/127.0.0.zone /var/lib/named/localhost.zone /var/lib/named/named.root.key /var/lib/named/root.hint

ENTRYPOINT ["{_entrypoint}"]
HEALTHCHECK --interval=10s --timeout=5s --retries=10 CMD ["{_healthcheck}"]

""",
    )
    for os_version in ALL_NONBASE_OS_VERSIONS
]
