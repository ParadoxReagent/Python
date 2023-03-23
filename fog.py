import sys
import os
import random
import string
import re
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


def random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def obfuscate_string_literals(code):
    string_pattern = re.compile(r'(\'[^\']*\'|"[^"]*")')
    return string_pattern.sub(lambda m: f"decrypt_string({m.group(0)}, b'{get_aes_key()}')", code)


def obfuscate_numeric_literals(code):
    num_pattern = re.compile(r'\b\d+\b')
    return num_pattern.sub(lambda m: f"({m.group(0)} ^ {random.randint(1, 100)} ^ {int(m.group(0)) % 2})", code)


def insert_dead_code(code):
    dead_code = '\n'.join([
        f"{random_string(10)} = {random.randint(-1000, 1000)}",
        f"{random_string(10)} = {random.randint(-1000, 1000)}",
        f"{random_string(10)} = {random.randint(-1000, 1000)}",
    ])
    return dead_code + '\n' + code


def obfuscate_control_flow(code):
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if random.random() < 0.2:
            new_lines.append(f"if {random.randint(0, 1)}: {random_string(10)} = {random.randint(-1000, 1000)}")
    return '\n'.join(new_lines)


def obfuscate_names(code):
    var_func_pattern = re.compile(r'\b(?<![\.])([a-zA-Z_][a-zA-Z0-9_]*)\b')
    names = set(re.findall(var_func_pattern, code))
    name_mapping = {name: random_string(10) for name in names}

    for name, obfuscated_name in name_mapping.items():
        code = re.sub(r'\b'+name+r'\b', obfuscated_name, code)

    return code


def outline_functions(code):
    def_pattern = re.compile(r'^def\s+(\w+)\s*\(', re.MULTILINE)
    funcs = re.findall(def_pattern, code)

    for func in funcs:
        code = re.sub(r'\b'+func+r'\b', random_string(10), code)

    return code


def inline_small_functions(code):
    func_pattern = re.compile(r'^def\s+(\w+)\s*\((.*?)\):\s*\n\s*(.+)\n$', re.MULTILINE | re.DOTALL)
    funcs = func_pattern.findall(code)

    for func in funcs:
        if len(func[2].strip().split('\n')) == 1:
            code = re.sub(r'\b'+func[0]+r'\b', '('+func[2].strip()+')', code)

    return code


def get_aes_key():
    return '0123456789abcdef0123456789abcdef'


def decrypt_string(enc_text, key):
    cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    decrypted = unpad(cipher.decrypt(base64.b64decode(enc_text)), 16)
    return decrypted.decode('utf-8')


def tamper_proof_and_anti_debug():
    tamper_proof_code = (
        'import os\n'
        'import sys\n'
        'import time\n'
        '\n'
        'def debugger_detection():\n'
        '    try:\n'
        '        import ctypes\n'
        '        if (ctypes.windll.kernel32.IsDebuggerPresent() != 0):\n'
        '            sys.exit(1)\n'
        '    except ImportError:\n'
        '        pass\n'
        '\n'
        'debugger_detection()\n'
        '\n'
        'def time_check():\n'
        '    t1 = time.time()\n'
        '    time.sleep(0.01)\n'
        '    t2 = time.time()\n'
        '    if t2 - t1 < 0.01:\n'
        '        sys.exit(1)\n'
        '\n'
        'time_check()\n'
    )
    return tamper_proof_code


def main():
    if len(sys.argv) != 3:
        print("Usage: python obfuscator.py <input_file> <output_file>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        return

    with open(input_file, 'r') as f:
        code = f.read()

    code = obfuscate_names(code)
    code = obfuscate_string_literals(code)
    code = obfuscate_numeric_literals(code)
    code = insert_dead_code(code)
    code = obfuscate_control_flow(code)
    code = outline_functions(code)
    code = inline_small_functions(code)

    encrypted_code = encrypt_string(code, get_aes_key())
    b64_encrypted_code = base64.b64encode(encrypted_code.encode('utf-8')).decode('utf-8')

    wrapped_code = f"""import base64

    def decrypt_string(enc_text, key):
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(base64.b64decode(enc_text)), 16)
        return decrypted.decode('utf-8')

    {tamper_proof_and_anti_debug()}

    aes_key = '{get_aes_key()}'
    encrypted_code = '{b64_encrypted_code}'
    decrypted_code = decrypt_string(encrypted_code, aes_key)
    exec(decrypted_code)
    """

    with open(output_file, 'w') as f:
        f.write(wrapped_code)

    print(f"Obfuscated and encrypted code saved to '{output_file}'")


if __name__ == "__main__":
    main()
