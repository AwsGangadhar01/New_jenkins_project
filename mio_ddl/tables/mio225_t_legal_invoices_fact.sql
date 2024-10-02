CREATE TABLE {pub_schema}.mio225_t_legal_invoices_fact
(	
 fact_guid  VARCHAR(64)   ENCODE RAW  
,fact_matter_guid  VARCHAR(64)   ENCODE lzo
,fact_matter_invoice_guid  VARCHAR(64)   ENCODE lzo
,fact_invoice_lineitem_guid  VARCHAR(64)   ENCODE lzo
,matter_ref VARCHAR(50)   ENCODE lzo
,matter VARCHAR(2000)   ENCODE lzo
,customer_matter_id VARCHAR(50)   ENCODE lzo
,department VARCHAR(500)   ENCODE lzo
,matter_vendors VARCHAR(5000)   ENCODE lzo
,internal_matter_lead_name VARCHAR(500)   ENCODE lzo
,no_of_days_since_last_invoice_uploaded  VARCHAR(50)   ENCODE lzo
,budget_in_customer_currency NUMERIC(15,2)   ENCODE az64
,average_blended_rate NUMERIC(15,2)   ENCODE az64
,no_of_invoice NUMERIC(5)   ENCODE az64
,duration_in_days  NUMERIC(10)   ENCODE az64
,no_of_timekeepers  NUMERIC(5)   ENCODE az64
,country VARCHAR(500)   ENCODE lzo
,region VARCHAR(50)   ENCODE lzo
,fee_type VARCHAR(500)   ENCODE lzo
,matter_expense_activity VARCHAR(1000)   ENCODE lzo 
,matter_open_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,matter_close_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,timekeeper_description VARCHAR(2000)   ENCODE lzo 
,invoice_id VARCHAR(2000)   ENCODE lzo
,purchase_order_number  VARCHAR(2000)   ENCODE lzo
,invoice_number  VARCHAR(2000)   ENCODE lzo
,invoice_payment_status  VARCHAR(2000)   ENCODE lzo 
,matter_category  VARCHAR(2000)   ENCODE lzo 
,entity  VARCHAR(2000)   ENCODE lzo
,invoice_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,tax  NUMERIC(15,2)   ENCODE az64
,discount NUMERIC(15,2)   ENCODE az64
,total_expenses NUMERIC(15,2)   ENCODE az64
,net_fees_total NUMERIC(15,2)   ENCODE az64
,gross_total NUMERIC(15,2)   ENCODE az64
,invoice_vendor  VARCHAR(2000)   ENCODE lzo
,billing_period_start_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,billing_period_end_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64 
,line_id   VARCHAR(50)   ENCODE lzo 
,line_type  VARCHAR(100)   ENCODE lzo
,line_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,adjusted_line_quantity  NUMERIC(5,2)    ENCODE az64
,line_unit_cost NUMERIC(15,2)   ENCODE az64
,adjusted_line_unit_cost NUMERIC(15,2)   ENCODE az64
,adjusted_line_amount NUMERIC(15,2)   ENCODE az64
,timekeeper_id   VARCHAR(50)   ENCODE lzo
,timekeeper  VARCHAR(2000)   ENCODE lzo
,role  VARCHAR(50)   ENCODE lzo
,role_group  VARCHAR(50)   ENCODE lzo
,line_invoice_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,matter_id VARCHAR(50)   ENCODE lzo
,invoice_status  VARCHAR(50)   ENCODE lzo
,billing_start_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,billing_end_date TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,expense_code  VARCHAR(50)   ENCODE lzo
,line_expense_activity  VARCHAR(1000)   ENCODE lzo
,activity_code  VARCHAR(2000)   ENCODE lzo
,vendor_ref  VARCHAR(2000)   ENCODE lzo
,mio_delete_ind VARCHAR(2)   ENCODE lzo
,record_type VARCHAR(256)   ENCODE lzo
,source_system_cde VARCHAR(50)   ENCODE lzo	
,mio_current_status BOOLEAN   ENCODE RAW
,mio_version_number INTEGER   ENCODE az64
,mio_created_by VARCHAR(2000)   ENCODE lzo
,mio_create_date_time TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,mio_updated_by VARCHAR(2000)   ENCODE lzo	
,mio_update_date_time TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
,mio_source_filename VARCHAR(2000)   ENCODE lzo
,mio_delta_hash VARCHAR(5000)   ENCODE lzo
,mio_version_valid_from DATE   ENCODE az64
,mio_version_valid_to DATE   ENCODE az64  
)
DISTSTYLE KEY
 DISTKEY (fact_guid)
 SORTKEY AUTO
