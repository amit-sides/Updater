# Updater
A utility to manage updates for a Windows program.

It allows a developer, of a windows software, to easily distribute it's software and deploy an update to it's clients.

It automatically creates a `setup.exe` file using `Inno Setup` that will install the software, and run a service that will listen on a UDP server for incoming updates. When the developer deploys a new update, the update server will broadcast an announcement message about the update to all the clients it can reach.

Each client that downloads the update can now transfer the update to other clients. This allows multiple distribution sources of the update, which reduces the overload on the update server. The updates are cryptographically signed using RSA, so the clients can't send a fake update and achieve RCE. 

This means that an organization with a LAN that is not exposed to the internet can still receive updates fairly easy. All it needs to do is create a server in the DMZ that will receive the updates from the official update server, and this server will update the clients inside the organization's LAN.

## Quick Usage

The guides assume that `python3` is the python 3 interpreter and that it is included in PATH. If you installed the `py` launcher, replace `python3` with `py -3`.

To quickly set up an update server and create your software's setup file, see the `Setup` and `Usage` sections in `Server\README.md`.

## Author Comment

I am sure there are far better solutions to this problem outside, but I liked working on this project and learnt a lot of new things:

* Working with sockets API in Python.
* Sending broadcast messages.
* Serializing Python types using the construct package.
* Creating a Windows service in Python.
* Using Python's crypto package to cryptographically sign data using RSA in a secure way.
* Using Python's registry API to read, write and delete registry keys and values.
* Converting a Python script to EXE executable using PyInstaller or cxFreeze.
* Creating a Windows setup installer for a program using Inno Setup (which apparently pretty much all the programs use).

