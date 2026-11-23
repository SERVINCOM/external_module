/** @odoo-module **/
export function isDescriptive(product, line) {
    return line.create_variant === 'no_variant' &&
        (product.servincom_descriptive_line_ids || []).includes(line.id);
}

export function clearDescriptiveSelections(product) {
    let changed = false;
    for (const line of product.attribute_lines) {
        if (isDescriptive(product, line) && line.selected_attribute_value_ids.length) {
            line.selected_attribute_value_ids = [];
            changed = true;
        }
    }
    return changed;
}
