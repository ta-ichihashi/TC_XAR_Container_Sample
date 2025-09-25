# About this Repository

This repository provides a step-by-step guide to build and deploy a containerized TwinCAT 3.1 XAR runtime environment using Docker on a Beckhoff IPC.

With this sample, you will learn how to:

- Build and configure a TwinCAT XAR container image.
- Set up secure communication using ADS-over-MQTT.
- Manage containers with Docker Compose and Makefile automation.
- Connect to the containerized TwinCAT runtime with TwinCAT Engineering.
- Configure real-time Ethernet communication (optional).

Here’s a high-level overview of what the completed setup will look like:

![](./docs/setup-overview.drawio.svg)

---

## How to get support

Should you have any questions regarding the provided sample code, please contact your local Beckhoff support team. Contact information can be found on the official Beckhoff website at https://www.beckhoff.com/contact/.

---

## Using the sample

Before you begin, make sure your environment meets the following prerequisites:

- [Setup and Install](https://infosys.beckhoff.com/english.php?content=../content/1033/beckhoff_rt_linux/17350447499.html) the Beckhoff Real-Time Linux® Distribution on a supported IPC.
- [Configure access to Beckhoff package server](https://infosys.beckhoff.com/english.php?content=../content/1033/beckhoff_rt_linux/17350408843.html)
- Install [Docker Engine on Debian](https://docs.docker.com/engine/install/debian/#install-using-the-repository)
- Run the following command to install the TwinCAT System Configuration tools and make on the host: `sudo apt install --yes make tcsysconf`

Once the prerequisites are in place, you can follow these steps to build and deploy the TwinCAT XAR container:

1. **Build the container image**

During the image build process, TwinCAT for Linux® will be downloaded from `https://deb.beckhoff.com`.
To access the package server replace `<mybeckhoff-mail>` and `<mybeckhoff-password>` in `./tc31-xar-base/apt-config/bhf.conf` with valid myBeckhoff credentials.

Furthermore, ensure that the file `./tc31-xar-base/apt-config/bhf.list` contains the correct Debian distribution codename of the current suite (e.g. `trixie-unstable` for beta versions).

Afterwards navigate to the `tc31-xar-base` directory and run:

```bash
sudo docker build --secret id=apt,src=./apt-config/bhf.conf --network host -t tc31-xar-base .
```

Alternatively the included `Makefile` can be used as wrapper for the most frequently used `docker` commands:

```bash
sudo make build-image
```

2. **Set up firewall rules for MQTT**

The sample will make use of **ADS-over-MQTT** for the communication between the TwinCAT XAR containers and the TwinCAT Engineering.
To establish ADS-over-MQTT communication allow incoming connections to the mosquitto broker which will be containerized in the next step.
To allow incoming connections, create `/etc/nftables.conf.d/60-mosquitto-container.conf` with the following content:

```
sudo nano /etc/nftables.conf.d/60-mosquitto-container.conf
```

```nft
table inet filter {
  chain input {
    tcp dport 1883 accept
  }
  chain forward {
    type filter hook forward priority 0; policy drop;
    tcp sport 1883 accept
    tcp dport 1883 accept
  }
}
```

Save the file by pressing <kbd>Ctrl</kbd>+<kbd>o</kbd> and <kbd>Enter</kbd>.
Then close the editor via <kbd>Ctrl</kbd>+<kbd>x</kbd> and <kbd>Enter</kbd>.

Apply the rules with the following command:

```bash
sudo nft -f /etc/nftables.conf.d/60-mosquitto-container.conf
```

3. **Start the containers**

The sample includes a `docker-compose.yml` file to simplify the process of creating a container network and starting the MQTT broker as well as the TwinCAT runtime container.
You can use the following command to setup the containers:

```bash
sudo docker compose up -d
```

4. **Configure ADS-over-MQTT connections**

To connect your TwinCAT Engineering system via ADS-over-MQTT with the containerized TwinCAT runtime use the `mqtt.xml` template.
In the file replace `ip-address-of-container-host` with the **IP address of the Docker host**.
Copy the adjusted file to:

```
C:\Program Files (x86)\Beckhoff\TwinCAT\3.1\Target\Routes\
```

Afterwards, restart the TwinCAT System Service.
The containerized TwinCAT runtime should appear as an available target system.

![](docs/choose-target-system.png)

5. **Configure real-time Ethernet**

Real-time Ethernet communication requires the `vfio-pci` driver for a PCI based network device. 
Use the command line tool `TcRteInstall` to assign the `vfio-pci` driver to network devices of the IPC.

1. List available network device for Real-Time Ethernet communication

```bash
sudo TcRteInstall -l
```
2. Assign the driver by passing the PCI device `Location`:

```bash
sudo TcRteInstall -b <PCI device Location>
```

3. Verify the assignment:

```bash
sudo TcRteInstall -l
```

4. For TwinCAT to detect the new configuration restart the TwinCAT runtime container via:

```
sudo make restart-containers
```
