# Dockerfile
FROM odoo:17.0

# Copy all 3 simple custom modules
COPY t29_custom_one /mnt/extra-addons/t29_custom_one
COPY t29_custom_2 /mnt/extra-addons/t29_custom_2
COPY t29_custom_3 /mnt/extra-addons/t29_custom_3

# Set proper permissions
USER root
RUN chown -R odoo:odoo /mnt/extra-addons
USER odoo

# Expose Odoo port
EXPOSE 8069
