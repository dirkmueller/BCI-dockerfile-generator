"""Build description for the milvus Container Images"""

import datetime

from bci_build.containercrate import ContainerCrate
from bci_build.os_version import CAN_BE_LATEST_OS_VERSION
from bci_build.os_version import OsVersion
from bci_build.package import DOCKERFILE_RUN
from bci_build.package import ApplicationStackContainer
from bci_build.package import OsContainer
from bci_build.package import Replacement
from bci_build.package import _build_tag_prefix
from bci_build.registry import publish_registry


MILVUS_CONTAINERS = [
    ApplicationStackContainer(
        name="milvus",
        package_name=(None if os_version.is_tumbleweed else "sac-milvus-cpu-image"),
        _publish_registry=publish_registry(os_version, app_collection=True),
        pretty_name="Milvus",
        custom_description=(
            "Milvus is a high-performance, highly scalable vector database that runs efficiently "
            "across a wide range of environments."
        )
        + (". It is {based_on_container}." if os_version.is_tumbleweed else "."),
        os_version=os_version,
        is_latest=(
            (os_version in CAN_BE_LATEST_OS_VERSION) and os_version.is_tumbleweed
        ),
        version="%%milvus_version%%",
        tag_version="2",
        version_in_uid=False,
        license="Apache-2.0",
        supported_until=datetime.date(2025, 12, 31),
        from_target_image=f"{_build_tag_prefix(os_version)}/bci-micro:{OsContainer.version_to_container_os_version(os_version)}",
        package_list=[
            "libglog-4-0",
            "etcd",
            "minio-client",
            "tini",
            "milvus",
            "milvus-cppcpu",
        ],
        replacements_via_service=[
            Replacement(
                regex_in_build_description="%%milvus_version%%", package_name="milvus"
            ),
        ],
        custom_end=rf"""{DOCKERFILE_RUN} mkdir /milvus && ln -s /etc/milvus/configs/ /milvus""",
        entrypoint=["/usr/bin/tini"],
        # logo_url="https://tomcat.apache.org/res/images/tomcat.png",
    )
    for os_version in (
        OsVersion.TUMBLEWEED,
        OsVersion.SP6,

    )
]

MILVUS_CRATE = ContainerCrate(MILVUS_CONTAINERS)
