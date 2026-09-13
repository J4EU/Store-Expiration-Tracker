#!/bin/bash
set -euo pipefail

device="/dev/sdf"
mount_point="/srv/store-expiration-tracker/data"

for attempt in $(seq 1 60); do
  if [ -b "${device}" ]; then
    echo "attempts: ${attempt}"
    break
  fi
  sleep 2
done

if [ ! -b "${device}" ]; then
  echo "Data EBS device ${device} did not appear" >&2
  exit 1
fi

filesystem_type="$(blkid -o value -s TYPE "${device}" || true)"
if [ -z "${filesystem_type}" ]; then
  signature="$(file -sL "${device}")"
  case "${signature}" in
    *": data")
      mkfs.xfs "${device}"
      filesystem_type="xfs"
      echo "Data EBS filesystem created: ${filesystem_type}"
      ;;
    *)
      echo "Data EBS has an unrecognized filesystem signature" >&2
      exit 1
      ;;
  esac
else
  echo "Data EBS filesystem detected: ${filesystem_type}; skipping mkfs"
fi

uuid="$(blkid -o value -s UUID "${device}")"
mkdir -p "${mount_point}"

if ! grep -qE "^UUID=${uuid}[[:space:]]+${mount_point}[[:space:]]" /etc/fstab; then
  echo "UUID=${uuid} ${mount_point} ${filesystem_type} defaults,nofail 0 2" >> /etc/fstab
fi

if ! mountpoint -q "${mount_point}"; then
  mount "${mount_point}"
fi
echo "Data EBS mounted at ${mount_point}"
