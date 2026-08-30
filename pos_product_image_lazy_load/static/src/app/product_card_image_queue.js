/** @odoo-module **/

import { onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

const MAX_CONCURRENT_IMAGE_LOADS = 8;
const pendingImageLoads = [];
let activeImageLoads = 0;

function processImageQueue() {
    while (activeImageLoads < MAX_CONCURRENT_IMAGE_LOADS && pendingImageLoads.length) {
        const imageLoad = pendingImageLoads.shift();
        if (imageLoad.cancelled) {
            continue;
        }

        activeImageLoads += 1;
        imageLoad.active = true;
        let released = false;
        imageLoad.release = () => {
            if (released) {
                return;
            }
            released = true;
            imageLoad.active = false;
            activeImageLoads -= 1;
            processImageQueue();
        };
        imageLoad.start(imageLoad.release);
    }
}

function enqueueImageLoad(start) {
    const imageLoad = {
        active: false,
        cancelled: false,
        release: null,
        start,
    };
    pendingImageLoads.push(imageLoad);
    processImageQueue();

    return () => {
        imageLoad.cancelled = true;
        if (imageLoad.active) {
            imageLoad.release();
        }
    };
}

patch(ProductCard.prototype, {
    setup() {
        super.setup(...arguments);
        this.deferredImageContainer = useRef("deferredImageContainer");
        this.deferredImageState = useState({ src: false });
        this.imageObserver = null;
        this.cancelImageLoad = null;
        this.releaseImageSlot = null;

        onMounted(() => this.observeDeferredImage());
        onWillUnmount(() => this.cleanupDeferredImage());
    },

    observeDeferredImage() {
        const container = this.deferredImageContainer.el;
        if (!container || !this.props.imageUrl) {
            return;
        }

        if (!("IntersectionObserver" in window)) {
            this.startDeferredImageLoad();
            return;
        }

        this.imageObserver = new window.IntersectionObserver(
            (entries) => {
                if (entries.some((entry) => entry.isIntersecting)) {
                    this.startDeferredImageLoad();
                }
            },
            {
                root: container.closest(".product-list"),
                rootMargin: "100px 0px",
                threshold: 0.01,
            }
        );
        this.imageObserver.observe(container);
    },

    startDeferredImageLoad() {
        if (this.cancelImageLoad || this.deferredImageState.src) {
            return;
        }
        this.imageObserver?.disconnect();
        this.cancelImageLoad = enqueueImageLoad((release) => {
            if (!this.deferredImageContainer.el) {
                release();
                return;
            }
            this.releaseImageSlot = release;
            this.deferredImageState.src = this.props.imageUrl;
        });
    },

    onDeferredImageSettled() {
        this.releaseImageSlot?.();
        this.releaseImageSlot = null;
        this.cancelImageLoad = null;
    },

    cleanupDeferredImage() {
        this.imageObserver?.disconnect();
        this.cancelImageLoad?.();
        this.cancelImageLoad = null;
        this.releaseImageSlot = null;
    },
});
