import pytest
from common import process
import time


@pytest.fixture()
def accel_pppd_config(veth_pair_netns):
    print("accel_pppd_config veth_pair_netns: " + str(veth_pair_netns))
    return (
        """
    [modules]
    pppoe
    auth_pap
    auth_chap_md5
    ippool
    radius

    [log]
    log-debug=/tmp/accel-ppp.log
    level=5
    log-file=/tmp/accel-ppp.log
    log-emerg=/tmp/accel-ppp.log
    log-fail-file=/tmp/accel-ppp.log
    
    [auth]
    any-login=0

    [ppp]
    verbose=5

    [radius]
    dictionary=/usr/local/share/accel-ppp/radius/dictionary
    nas-identifier=accel-ppp
    nas-ip-address=127.0.0.1
    gw-ip-address=192.168.1.1
    server=127.0.0.1,testing123,auth-port=1812,acct-port=1813,req-limit=10,fail-time=0
    #dae-server=127.0.0.1:3799
    verbose=5
    timeout=20
    max-try=1
    acct-interval=60
    acct-timeout=120

    [ip-pool]
    gw-ip-address=192.0.2.1
    192.0.2.2-255

    [cli]
    tcp=127.0.0.1:2001

    [pppoe]
    verbose=5
    #ifname-in-sid=both
    ifname-in-sid=calling-sid
    interface="""
        + veth_pair_netns["veth_a"]
    )


@pytest.fixture()
def pppd_config(veth_pair_netns):
    # HACK /etc/ppp/pap-secrets
    with open("/etc/ppp/pap-secrets", "w") as f:
        f.write("loginAB * pass123 *")
    # HACK /etc/ppp/chap-secrets
    with open("/etc/ppp/chap-secrets", "w") as f:
        f.write("loginAB * pass123 *")

    print("pppd_config veth_pair_netns: " + str(veth_pair_netns))
    return (
        """
    nodetach
    noipdefault
    defaultroute   
    noauth
    connect /bin/true
    persist
    mtu 1492
    noaccomp
    default-asyncmap
    name loginAB
    plugin rp-pppoe.so
    nic-"""
        + veth_pair_netns["veth_b"]
    )

# tcpdump args
@pytest.fixture()
def tcpdump_args():
    return ["-n", "-vvv", "-i", "lo", "udp"]

# test pppoe session over radius
def test_pppoe_session_radius(pppd_instance, tcpdump_instance, accel_cmd, accel_pppd_instance):

    # start tcpdump
    assert tcpdump_instance["is_started"]

    # test that pppd (with accel-pppd) started successfully
    assert pppd_instance["is_started"]

    # wait until session is started
    max_wait_time = 10.0
    sleep_time = 0.0
    is_started = False  # is session started
    while sleep_time < max_wait_time:
        (exit, out, err) = process.run(
            [
                accel_cmd,
                "show stat",
            ]
        )
        assert exit == 0  # accel-cmd fails
        #print(out)
        if "auth sent: 1" in out:
            # session is found
            print(
                "test_pppoe_session_radius: radius auth sent in (sec): " + str(sleep_time)
            )
            #is_started = True
            break
        #if "loginAB" in out and "192.0.2." in out and "active" in out:
        #    # session is found
        #    print(
        #        "test_pppoe_session_radius: session found in (sec): " + str(sleep_time)
        #    )
        #    is_started = True
        #    break
        time.sleep(0.1)
        sleep_time += 0.1

    print("test_pppoe_session_radius: last accel-cmd out: " + out)
    # print out /tmp/accel-ppp.log
    (exit, out, err) = process.run(["cat", "/tmp/accel-ppp.log"])
    assert exit == 0  # cat fails
    print("test_pppoe_session_radius: last /tmp/accel-ppp.log: " + out)


    # test that session is started
    assert is_started == True
