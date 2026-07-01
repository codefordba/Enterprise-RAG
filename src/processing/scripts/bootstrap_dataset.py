import os
import requests

DATASETS = {

    "TechSupport": {

        "NVIDIA": [

            ("H100_Architecture.pdf",
             "https://resources.nvidia.com/en-us-tensor-core/nvidia-h100-architecture-whitepaper"),

            ("TensorRT-LLM.pdf",
             "https://developer.download.nvidia.com/assets/cuda/files/TensorRT-LLM-Whitepaper.pdf"),
        ],

        "Oracle": [

            ("OCI_AI.pdf",
             "https://docs.oracle.com/en/cloud/ai-services/")
        ]
    },

    "Legal": {

        "GDPR": [

            ("GDPR.pdf",
             "https://gdpr-info.eu/")
        ]
    }

}


def download(url, filename):

    try:

        r = requests.get(url, timeout=60)

        if r.status_code == 200:

            with open(filename, "wb") as f:
                f.write(r.content)

            print(f"Downloaded {filename}")

        else:

            print(f"Failed {url}")

    except Exception as e:

        print(e)


def main():

    base = "sample_data"

    os.makedirs(base, exist_ok=True)

    for tenant in DATASETS:

        tenant_path = os.path.join(base, tenant)

        os.makedirs(tenant_path, exist_ok=True)

        for vendor in DATASETS[tenant]:

            vendor_path = os.path.join(tenant_path, vendor)

            os.makedirs(vendor_path, exist_ok=True)

            for pdf, url in DATASETS[tenant][vendor]:

                outfile = os.path.join(vendor_path, pdf)

                if not os.path.exists(outfile):

                    download(url, outfile)


if __name__ == "__main__":
    main()
    