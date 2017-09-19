import os
import shutil
import argparse
import arvados

project_uuid = "qr1hi-j7d0g-u5mez5ad2fb3gn8"
api = arvados.api('v1')

parser = argparse.ArgumentParser()
parser.add_argument("output_dir", help="Output directory to upload to arvados")
args = parser.parse_args()
print(args)
out = arvados.CollectionWriter()

print("Writing %s to Collection" % (args.output_dir))
out.write_directory_tree(args.output_dir)
out.finish_current_stream()
print("Current Collection: \nPDH: %s\n\nManifest text: %s\n\n" % (out.portable_data_hash(), out.manifest_text()))
print("Removing %s to save space" % (args.output_dir))
shutil.rmtree(args.output_dir)

coll_id = out.finish()
print(coll_id)
collection_body = {
    "collection": {
        "name":"Test data",
        "owner_uuid":project_uuid,
        "portable_data_hash":out.portable_data_hash(),
        "manifest_text":out.manifest_text()
    }
}
result = api.collections().create(body=collection_body).execute()
print(result)
