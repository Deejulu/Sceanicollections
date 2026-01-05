/**
 * SceaniCollections - AJAX Cart Functionality
 * Handles all cart operations without page refresh
 */

class CartManager {
    constructor() {
        this.init();
    }

    init() {
        // Initialize cart forms
        this.initAddToCartForms();
        this.initCartPage();
        this.initWishlistToggle();
    }

    // Get CSRF token from cookies
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Show toast notification
    showToast(message, type = 'success') {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.cart-toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `cart-toast fixed top-20 right-4 z-[9999] px-6 py-4 rounded-lg shadow-2xl transform transition-all duration-300 translate-x-full flex items-center space-x-3 max-w-sm`;
        
        if (type === 'success') {
            toast.classList.add('bg-green-600', 'text-white');
            toast.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-check text-white"></i>
                </div>
                <span class="text-sm font-medium">${message}</span>
            `;
        } else if (type === 'error') {
            toast.classList.add('bg-red-600', 'text-white');
            toast.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-times text-white"></i>
                </div>
                <span class="text-sm font-medium">${message}</span>
            `;
        } else {
            toast.classList.add('bg-scent-blue', 'text-white');
            toast.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-shopping-cart text-scent-blue"></i>
                </div>
                <span class="text-sm font-medium">${message}</span>
            `;
        }

        document.body.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full');
            toast.classList.add('translate-x-0');
        });

        // Auto dismiss after 3 seconds
        setTimeout(() => {
            toast.classList.remove('translate-x-0');
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Update cart badge in navbar
    updateCartBadge(count) {
        const badges = document.querySelectorAll('[data-cart-count], .cart-badge');
        badges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });

        // Also update any cart total items display
        const totalDisplays = document.querySelectorAll('[data-cart-total-items]');
        totalDisplays.forEach(el => {
            el.textContent = count;
        });
    }

    // Initialize Add to Cart forms
    initAddToCartForms() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.matches('form[action*="/cart/add/"]') || form.classList.contains('add-to-cart-form')) {
                e.preventDefault();
                this.handleAddToCart(form);
            }
        });

        // Also handle click on add-to-cart buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.add-to-cart-btn');
            if (btn && !btn.closest('form')) {
                e.preventDefault();
                const productId = btn.dataset.productId;
                const quantity = btn.dataset.quantity || 1;
                if (productId) {
                    this.addToCart(productId, quantity);
                }
            }
        });
    }

    // Handle Add to Cart form submission
    async handleAddToCart(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalContent = submitBtn ? submitBtn.innerHTML : '';
        
        // Show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Adding...';
        }

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showToast(data.message, 'cart');
                this.updateCartBadge(data.cart_total_items);
                
                // Animate the button
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-check mr-2"></i> Added!';
                    submitBtn.classList.add('bg-green-600');
                    setTimeout(() => {
                        submitBtn.innerHTML = originalContent;
                        submitBtn.classList.remove('bg-green-600');
                        submitBtn.disabled = false;
                    }, 1500);
                }
            } else {
                this.showToast(data.message || 'Error adding to cart', 'error');
                if (submitBtn) {
                    submitBtn.innerHTML = originalContent;
                    submitBtn.disabled = false;
                }
            }
        } catch (error) {
            console.error('Cart error:', error);
            this.showToast('Something went wrong. Please try again.', 'error');
            if (submitBtn) {
                submitBtn.innerHTML = originalContent;
                submitBtn.disabled = false;
            }
        }
    }

    // Direct add to cart
    async addToCart(productId, quantity = 1) {
        const formData = new FormData();
        formData.append('quantity', quantity);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        try {
            const response = await fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showToast(data.message, 'cart');
                this.updateCartBadge(data.cart_total_items);
            } else {
                this.showToast(data.message || 'Error adding to cart', 'error');
            }
        } catch (error) {
            console.error('Cart error:', error);
            this.showToast('Something went wrong. Please try again.', 'error');
        }
    }

    // Initialize cart page functionality
    initCartPage() {
        // Quantity increment/decrement buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-quantity-btn]');
            if (btn) {
                e.preventDefault();
                const action = btn.dataset.quantityBtn;
                const itemId = btn.dataset.itemId;
                const input = document.querySelector(`input[data-quantity-input="${itemId}"]`);
                
                if (input) {
                    let currentValue = parseInt(input.value) || 1;
                    
                    if (action === 'increase') {
                        currentValue++;
                    } else if (action === 'decrease') {
                        currentValue = Math.max(1, currentValue - 1);
                    }
                    
                    input.value = currentValue;
                    this.updateCartItem(itemId, currentValue);
                }
            }
        });

        // Quantity input change
        document.addEventListener('change', (e) => {
            const input = e.target;
            if (input.matches('[data-quantity-input]')) {
                const itemId = input.dataset.quantityInput;
                const quantity = Math.max(1, parseInt(input.value) || 1);
                input.value = quantity;
                this.updateCartItem(itemId, quantity);
            }
        });

        // Remove item buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-remove-item]');
            if (btn) {
                e.preventDefault();
                const itemId = btn.dataset.removeItem;
                this.removeCartItem(itemId);
            }
        });

        // Remove form submissions for cart remove
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.matches('form[action*="/cart/remove/"]')) {
                e.preventDefault();
                const action = form.action;
                const itemId = action.match(/\/cart\/remove\/(\d+)/)?.[1];
                if (itemId) {
                    this.removeCartItem(itemId);
                }
            }
        });

        // Clear cart
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-clear-cart]');
            if (btn) {
                e.preventDefault();
                if (confirm('Are you sure you want to clear your cart?')) {
                    this.clearCart();
                }
            }
        });
    }

    // Update cart item quantity
    async updateCartItem(itemId, quantity) {
        const formData = new FormData();
        formData.append('quantity', quantity);
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        const row = document.querySelector(`[data-cart-item="${itemId}"]`);
        if (row) {
            row.style.opacity = '0.6';
        }

        try {
            const response = await fetch(`/cart/update/${itemId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                if (data.removed) {
                    // Item was removed
                    this.removeCartItemFromDOM(itemId);
                    this.showToast(data.message, 'success');
                } else {
                    // Update item total
                    const itemTotal = document.querySelector(`[data-item-total="${itemId}"]`);
                    if (itemTotal) {
                        itemTotal.textContent = `₦${data.item_total.toLocaleString('en-NG', {minimumFractionDigits: 2})}`;
                    }
                }
                
                this.updateCartBadge(data.cart_total_items);
                this.updateCartSummary(data.cart_subtotal);
                
            } else {
                this.showToast(data.message || 'Error updating cart', 'error');
            }
        } catch (error) {
            console.error('Cart update error:', error);
            this.showToast('Something went wrong. Please try again.', 'error');
        } finally {
            if (row) {
                row.style.opacity = '1';
            }
        }
    }

    // Remove cart item
    async removeCartItem(itemId) {
        const row = document.querySelector(`[data-cart-item="${itemId}"]`);
        if (row) {
            row.style.opacity = '0.5';
            row.style.transform = 'scale(0.98)';
        }

        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        try {
            const response = await fetch(`/cart/remove/${itemId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.removeCartItemFromDOM(itemId);
                this.updateCartBadge(data.cart_total_items);
                this.updateCartSummary(data.cart_subtotal);
                this.showToast(data.message, 'success');
                
                // Check if cart is empty
                if (data.cart_total_items === 0) {
                    this.showEmptyCart();
                }
            } else {
                this.showToast(data.message || 'Error removing item', 'error');
                if (row) {
                    row.style.opacity = '1';
                    row.style.transform = 'scale(1)';
                }
            }
        } catch (error) {
            console.error('Cart remove error:', error);
            this.showToast('Something went wrong. Please try again.', 'error');
            if (row) {
                row.style.opacity = '1';
                row.style.transform = 'scale(1)';
            }
        }
    }

    // Remove item from DOM with animation
    removeCartItemFromDOM(itemId) {
        const row = document.querySelector(`[data-cart-item="${itemId}"]`);
        if (row) {
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            setTimeout(() => row.remove(), 300);
        }
    }

    // Clear entire cart
    async clearCart() {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        try {
            const response = await fetch('/cart/clear/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.updateCartBadge(0);
                this.showEmptyCart();
                this.showToast(data.message, 'success');
            } else {
                this.showToast(data.message || 'Error clearing cart', 'error');
            }
        } catch (error) {
            console.error('Cart clear error:', error);
            this.showToast('Something went wrong. Please try again.', 'error');
        }
    }

    // Update cart summary totals
    updateCartSummary(subtotal) {
        const subtotalEl = document.querySelector('[data-cart-subtotal]');
        if (subtotalEl) {
            subtotalEl.textContent = `₦${subtotal.toLocaleString('en-NG', {minimumFractionDigits: 2})}`;
        }

        // Update total (subtotal + shipping if applicable)
        const totalEl = document.querySelector('[data-cart-total]');
        const shippingEl = document.querySelector('[data-shipping-cost]');
        
        if (totalEl) {
            let total = subtotal;
            if (shippingEl) {
                const shippingText = shippingEl.textContent.replace(/[₦,]/g, '');
                const shipping = parseFloat(shippingText) || 0;
                total += shipping;
            }
            totalEl.textContent = `₦${total.toLocaleString('en-NG', {minimumFractionDigits: 2})}`;
        }
    }

    // Show empty cart state
    showEmptyCart() {
        const cartContainer = document.querySelector('[data-cart-container]');
        if (cartContainer) {
            cartContainer.innerHTML = `
                <div class="text-center py-16">
                    <div class="w-24 h-24 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-6">
                        <i class="fas fa-shopping-cart text-gray-300 text-4xl"></i>
                    </div>
                    <h2 class="text-xl font-bold text-gray-900 mb-2">Your Cart is Empty</h2>
                    <p class="text-gray-500 mb-6">Looks like you haven't added any items to your cart yet.</p>
                    <a href="/store/" class="inline-flex items-center px-6 py-3 bg-scent-blue text-white rounded-lg font-medium hover:bg-opacity-90 transition">
                        <i class="fas fa-shopping-bag mr-2 text-amber-500"></i> Start Shopping
                    </a>
                </div>
            `;
        }
    }

    // Initialize wishlist toggle
    initWishlistToggle() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-wishlist-toggle]');
            if (btn) {
                e.preventDefault();
                const productId = btn.dataset.wishlistToggle;
                this.toggleWishlist(productId, btn);
            }
        });
    }

    // Toggle wishlist
    async toggleWishlist(productId, btn) {
        const originalIcon = btn.querySelector('i');
        const wasInWishlist = originalIcon?.classList.contains('fas');

        // Optimistic UI update
        if (originalIcon) {
            originalIcon.classList.toggle('fas');
            originalIcon.classList.toggle('far');
            originalIcon.classList.toggle('text-red-500');
        }

        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCsrfToken());

        try {
            const response = await fetch(`/dashboard/customer/wishlist/toggle/${productId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showToast(data.message, 'success');
            } else {
                // Revert UI on error
                if (originalIcon) {
                    originalIcon.classList.toggle('fas');
                    originalIcon.classList.toggle('far');
                    originalIcon.classList.toggle('text-red-500');
                }
                this.showToast(data.message || 'Error updating wishlist', 'error');
            }
        } catch (error) {
            console.error('Wishlist error:', error);
            // Revert UI on error
            if (originalIcon) {
                originalIcon.classList.toggle('fas');
                originalIcon.classList.toggle('far');
                originalIcon.classList.toggle('text-red-500');
            }
            this.showToast('Something went wrong. Please try again.', 'error');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cartManager = new CartManager();
});
