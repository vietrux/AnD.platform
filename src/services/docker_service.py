import uuid
import asyncio
import zipfile
import shutil
from pathlib import Path
import docker
from docker.errors import DockerException, ImageNotFound

from src.core.config import get_settings
from src.core.exceptions import DockerError


def get_docker_client():
    settings = get_settings()
    return docker.from_env()


async def extract_vulnbox(game_id: uuid.UUID, zip_content: bytes) -> str:
    settings = get_settings()
    vulnbox_dir = Path(settings.upload_dir) / "vulnboxes" / str(game_id)
    vulnbox_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = vulnbox_dir / "vulnbox.zip"
    zip_path.write_bytes(zip_content)
    
    extract_dir = vulnbox_dir / "source"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()
    
    def _extract():
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    
    await asyncio.to_thread(_extract)
    
    return str(extract_dir)


async def build_vulnbox_image(game_id: uuid.UUID, source_path: str) -> str:
    image_tag = f"adg-vulnbox-{game_id}"
    
    def _build():
        client = get_docker_client()
        dockerfile_path = Path(source_path)
        
        if not (dockerfile_path / "Dockerfile").exists():
            subdirs = [d for d in dockerfile_path.iterdir() if d.is_dir()]
            if subdirs and (subdirs[0] / "Dockerfile").exists():
                dockerfile_path = subdirs[0]
        
        if not (dockerfile_path / "Dockerfile").exists():
            raise DockerError(f"Dockerfile not found in {source_path}")
        
        client.images.build(
            path=str(dockerfile_path),
            tag=image_tag,
            rm=True,
        )
        return image_tag
    
    return await asyncio.to_thread(_build)


async def deploy_team_container(
    game_id: uuid.UUID,
    team_id: str,
    image_tag: str,
) -> tuple[str, str]:
    container_name = f"adg-{game_id}-{team_id}"
    
    def _deploy():
        client = get_docker_client()
        
        try:
            existing = client.containers.get(container_name)
            existing.remove(force=True)
        except docker.errors.NotFound:
            pass
        
        container = client.containers.run(
            image_tag,
            name=container_name,
            detach=True,
            network_mode="bridge",
            auto_remove=False,
        )
        
        container.reload()
        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        ip_address = "unknown"
        for network_info in networks.values():
            ip_address = network_info.get("IPAddress", "unknown")
            break
        
        return container_name, ip_address
    
    return await asyncio.to_thread(_deploy)


async def stop_team_container(container_name: str) -> None:
    def _stop():
        client = get_docker_client()
        try:
            container = client.containers.get(container_name)
            container.stop(timeout=10)
            container.remove()
        except docker.errors.NotFound:
            pass
    
    await asyncio.to_thread(_stop)


async def inject_flag_to_container(
    container_name: str,
    flag_value: str,
    flag_path: str,
) -> bool:
    def _inject():
        client = get_docker_client()
        try:
            container = client.containers.get(container_name)
            container.exec_run(f"sh -c 'echo {flag_value} > {flag_path}'")
            return True
        except docker.errors.NotFound:
            return False
    
    return await asyncio.to_thread(_inject)
