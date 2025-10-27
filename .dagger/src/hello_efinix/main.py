from typing import Annotated
import dagger
from dagger import dag, function, object_type


TARGET_DIR="/usr/local"


@object_type
class HelloEfinix:

    repository: str = "ghcr.io/scs-kno"
    repo_host: str = "ghcr.io"
    repo_user: str = "scs-kno"
    installer: str = "https://www.efinixinc.com/dl/efinity-2025.1.110-linux-x64.tar.bz2"
    efinity_version: str = "2025.1.110"

    certs = dag.cache_volume("certs")
    docker = dag.cache_volume("docker")

    @function
    def container_echo(self, string_arg: str) -> dagger.Container:
        """Returns a container that echoes whatever string argument is provided"""
        return dag.container().from_("alpine:latest").with_exec(["echo", string_arg])

    async def efinity_sw_deps(self) -> dagger.Container:
        version = "24.04"
        ubuntu = dag.container().from_(f"ubuntu:{version}")

        return (
            ubuntu.with_exec(["apt", "update"])
            .with_exec(["apt", "install", "-y", "default-jre",])
            .with_exec(["apt", "install", "-y", "libxcb-cursor0"])
            .with_exec(["apt", "install", "-y", "bzip2"])
            .with_exec(["apt", "install", "-y", "git"])
            .with_exec(["apt", "install", "-y", "locales"])
            .with_exec(["locale-gen", "en_US.UTF-8"])
            .with_env_variable("LANG", "en_US.UTF-8")
        )

    @function
    async def efinity_installer(self) -> dagger.Container:
        """Create a container containing the installation sources"""
        ubuntu = await self.efinity_sw_deps()
        src: dagger.File = dag.http(self.installer)

        return (
            ubuntu.with_mounted_file("/tmp/effinity.tar.bz2", src)
            .with_workdir(str(TARGET_DIR))
            .with_exec(
                [
                    "tar",
                    "-xvjf",
                    "/tmp/effinity.tar.bz2",
                    "-C",
                    str(TARGET_DIR),
                ]
            )
            .with_env_variable("PATH", TARGET_DIR +
                               "/efinity/2025.1/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
        )


    @function
    async def efinity_publish(
        self,
        token: Annotated[dagger.Secret, dagger.Doc("API token")],
    ) -> str:
        """Create the questa base installation and publish it"""
        efinity = await self.efinity_installer()
        return (
                await efinity
                .with_registry_auth(self.repo_host, self.repo_user, token)
                .publish(f"{self.repository}/efinity:{self.efinity_version}")
               )

    @function
    async def efinity(
            self,
            token: Annotated[dagger.Secret, dagger.Doc("API token")],
    ) -> dagger.Container:
        """Return the efinity container from the scs repoistory"""
        efinity = (
                dag
                .container()
                .with_registry_auth(self.repo_host, self.repo_user, token)
                #.from_(f"{self.repository}/efinity:{self.efinity_version}")
               .from_(f"{self.repository}/efinix:latest"))
        return efinity
