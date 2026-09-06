-- parse the messy dimension (-- →null, 50+ ratings→50, ₹ 200→200, city after last comma):

select 
    id::number as restaurant_id, 
    name as restaurant_name,
    -- Keep only the last part of the comma-separated city value.
    trim(coalesce(regexp_substr(city, '[^,]+$'), city)) as city,
    -- Turn '--' into null and cast the rating to a decimal.
    try_to_decimal(nullif(rating, '--'), 3, 1) as rating,
    -- Pull the numeric value out of the rating count text.
    try_to_number(regexp_substr(rating_count, '[0-9]+')) as rating_count,
    -- Pull the numeric value out of the cost text.
    try_to_number(regexp_substr(cost, '[0-9]+')) as cost_for_two,
    cuisine, 
    lic_no as license_no
from {{ source('raw', 'restaurants') }} where try_to_number(id) is not null