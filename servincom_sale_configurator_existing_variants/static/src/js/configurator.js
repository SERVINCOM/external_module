/** @odoo-module **/
import { patch } from '@web/core/utils/patch';
import { Mutex } from '@web/core/utils/concurrency';
import { Product } from '@sale/js/product/product';
import { ProductConfiguratorDialog } from '@sale/js/product_configurator_dialog/product_configurator_dialog';
import { ProductTemplateAttributeLine } from '@sale/js/product_template_attribute_line/product_template_attribute_line';
import { isDescriptive, clearDescriptiveSelections } from './descriptive';
import { hasExistingSelection, normalizeSelection, updateVisibility } from './combinations';

patch(Product, {
    props: {
        ...Product.props,
        servincom_combinations: {type: Array, optional: true},
        servincom_descriptive_line_ids: {type: Array, optional: true},
    },
});
patch(Product.prototype, {
    shouldShowPtal(line) {
        return !isDescriptive(this.props, line) && super.shouldShowPtal(line);
    },
});
const valueProp = ProductTemplateAttributeLine.props.attribute_values;
patch(ProductTemplateAttributeLine, {
    props: {
        ...ProductTemplateAttributeLine.props,
        attribute_values: {
            ...valueProp,
            element: {
                ...valueProp.element,
                shape: {...valueProp.element.shape, servincomHidden: {type: Boolean, optional: true}},
            },
        },
    },
});

patch(ProductConfiguratorDialog.prototype, {
    async _loadData(...args) {
        const data = await super._loadData(...args);
        this.currency.id ??= data.currency_id;
        const products = [...data.products, ...data.optional_products];
        for (const product of products) {
            const cleared = clearDescriptiveSelections(product);
            if (!Array.isArray(product.servincom_combinations)) {
                if (cleared) {
                    Object.assign(product, await this._updateCombination(product, product.quantity));
                }
                continue;
            }
            const parent = products.find((p) => p.product_tmpl_id === product.parent_product_tmpl_id);
            const parents = parent ? this._getCombination(parent) : [];
            const normalized = normalizeSelection(product, parents);
            if ((cleared || normalized) && hasExistingSelection(product)) {
                Object.assign(product, await this._updateCombination(product, product.quantity));
            }
            updateVisibility(product, parents);
        }
        return data;
    },

    async _getOptionalProducts(...args) {
        const products = await super._getOptionalProducts(...args);
        for (const product of products) {
            if (clearDescriptiveSelections(product)) {
                Object.assign(product, await this._updateCombination(product, product.quantity));
            }
        }
        return products;
    },

    _getCombination(product) {
        clearDescriptiveSelections(product);
        return super._getCombination(product);
    },

    _checkExclusions(product) {
        super._checkExclusions(product);
        if (Array.isArray(product.servincom_combinations)) {
            updateVisibility(product, this._getParentsCombination(product));
        }
    },

    async _updateProductTemplateSelectedPTAV(productId, lineId, valueId, isMulti) {
        const product = this._findProduct(productId);
        if (!Array.isArray(product.servincom_combinations)) {
            return super._updateProductTemplateSelectedPTAV(productId, lineId, valueId, isMulti);
        }
        this.servincomMutex ||= new Mutex();
        this.state.servincomPending = (this.state.servincomPending || 0) + 1;
        try {
            return await this.servincomMutex.exec(async () => {
                const line = product.attribute_lines.find((item) => item.id === lineId);
                if (line.create_variant !== 'no_variant' && !isMulti) {
                    line.selected_attribute_value_ids = [Number(valueId)];
                    normalizeSelection(product, this._getParentsCombination(product));
                    valueId = line.selected_attribute_value_ids[0];
                }
                return super._updateProductTemplateSelectedPTAV(productId, lineId, valueId, isMulti);
            });
        } finally {
            this.state.servincomPending--;
        }
    },

    _isPossibleCombination(product) {
        return super._isPossibleCombination(product) &&
            (!Array.isArray(product.servincom_combinations) ||
                (Boolean(product.id) && hasExistingSelection(product)));
    },

    isPossibleConfiguration() {
        return !this.state.servincomPending && super.isPossibleConfiguration();
    },
});
