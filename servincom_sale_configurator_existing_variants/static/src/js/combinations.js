/** @odoo-module **/

export function variantLines(product) {
    return product.attribute_lines.filter((line) => line.create_variant !== 'no_variant');
}

export function compatibleRows(product, parents = []) {
    const informational = product.attribute_lines
        .filter((line) => line.create_variant === 'no_variant')
        .flatMap((line) => line.selected_attribute_value_ids);
    return product.servincom_combinations.filter((row) => {
        const selection = new Set([...row, ...informational]);
        for (const id of selection) {
            if ((product.exclusions?.[id] || []).some((other) => selection.has(other))) {
                return false;
            }
        }
        return !parents.some((id) =>
            (product.parent_exclusions?.[id] || []).some((other) => selection.has(other))
        );
    });
}

// Earlier attributes drive later ones, so switching the type remains possible
// even when its capacities do not overlap the previous type's capacities.
export function normalizeSelection(product, parents = []) {
    let rows = compatibleRows(product, parents);
    let changed = false;
    for (const line of variantLines(product)) {
        const allowed = new Set(rows.flat());
        const current = line.selected_attribute_value_ids[0];
        const choice = allowed.has(current) ? current :
            line.attribute_values.find((value) => allowed.has(value.id))?.id;
        if (choice === undefined) {
            return changed;
        }
        if (current !== choice) {
            line.selected_attribute_value_ids = [choice];
            changed = true;
        }
        rows = rows.filter((row) => row.includes(choice));
    }
    return changed;
}

export function updateVisibility(product, parents = []) {
    let rows = compatibleRows(product, parents);
    for (const line of variantLines(product)) {
        const allowed = new Set(rows.flat());
        for (const value of line.attribute_values) {
            value.servincomHidden = !allowed.has(value.id);
            value.excluded = value.servincomHidden;
        }
        rows = rows.filter((row) => line.selected_attribute_value_ids.every((id) => row.includes(id)));
    }
}

export function hasExistingSelection(product) {
    const selected = variantLines(product).flatMap((line) => line.selected_attribute_value_ids);
    return product.servincom_combinations.some((row) =>
        row.length === selected.length && selected.every((id) => row.includes(id))
    );
}
