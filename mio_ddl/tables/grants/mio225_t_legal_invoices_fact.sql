ALTER TABLE {pub_schema}.mio225_t_legal_invoices_fact owner to mio_glue_system;
GRANT INSERT, SELECT, UPDATE, DELETE, RULE, REFERENCES, TRIGGER ON TABLE {pub_schema}.mio225_t_legal_invoices_fact TO mio_glue_system;
GRANT SELECT ON TABLE {pub_schema}.mio225_t_legal_invoices_fact TO group grp_support;