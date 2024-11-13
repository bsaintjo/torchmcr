import pytest
import torch
import torch.nn.functional as F
from torchmcr.loss_models.smooth_loss import CustomLoss

@pytest.fixture
def loss_inputs():
    """Fixture providing test input tensors"""
    predicted = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    target = torch.tensor([[1.1, 2.1, 3.1], [3.9, 4.9, 5.9]])
    spectra = torch.tensor([[0.5, 1.0, 1.5], [2.0, 2.5, 3.0]])
    return predicted, target, spectra

def test_custom_loss_initialization():
    """Test CustomLoss initialization with different parameters"""
    # Test default initialization
    loss_fn = CustomLoss()
    assert loss_fn.base_loss_fn == F.l1_loss
    assert loss_fn.smooth_spectra_weight == 0.1
    assert loss_fn.smooth_weight_weight == 0.1
    
    # Test custom initialization
    loss_fn = CustomLoss(
        base_loss_fn=F.mse_loss,
        smooth_spectra_weight=0.2,
        smooth_weight_weight=0.3
    )
    assert loss_fn.base_loss_fn == F.mse_loss
    assert loss_fn.smooth_spectra_weight == 0.2
    assert loss_fn.smooth_weight_weight == 0.3

def test_custom_loss_forward(loss_inputs):
    """Test forward pass of CustomLoss"""
    predicted, target, spectra = loss_inputs
    loss_fn = CustomLoss()
    
    # Test basic forward pass
    loss = loss_fn(predicted, target, spectra)
    assert isinstance(loss, torch.Tensor)
    assert loss.ndim == 0  # Should be a scalar
    assert loss.item() > 0  # Loss should be positive

def test_custom_loss_scale_invariance(loss_inputs):
    """Test that loss scales predictably with input magnitude"""
    predicted, target, spectra = loss_inputs
    loss_fn = CustomLoss()
    
    # Compute loss with original inputs
    original_loss = loss_fn(predicted, target, spectra)
    
    # Scale all inputs by the same factor
    scale_factor = 10.0
    scaled_loss = loss_fn(
        predicted * scale_factor, 
        target * scale_factor, 
        spectra * scale_factor
    )
    
    # Loss should scale approximately with the scale factor
    # Allow for some variation due to the smoothness terms
    ratio = scaled_loss / original_loss
    assert 0.5 * scale_factor < ratio < 1.5 * scale_factor

def test_custom_loss_smoothness_penalties(loss_inputs):
    """Test that smoothness penalties affect the loss appropriately"""
    predicted, target, spectra = loss_inputs
    
    # Create loss functions with different smoothness weights
    loss_fn_base = CustomLoss(smooth_spectra_weight=0.0, smooth_weight_weight=0.0)
    loss_fn_smooth = CustomLoss(smooth_spectra_weight=1.0, smooth_weight_weight=1.0)
    
    base_loss = loss_fn_base(predicted, target, spectra)
    smooth_loss = loss_fn_smooth(predicted, target, spectra)
    
    # Loss with smoothness penalties should be larger
    assert smooth_loss > base_loss

def test_custom_loss_gradients(loss_inputs):
    """Test that loss produces valid gradients"""
    predicted, target, spectra = loss_inputs
    
    # Make inputs require gradients
    predicted.requires_grad_(True)
    spectra.requires_grad_(True)
    
    loss_fn = CustomLoss()
    loss = loss_fn(predicted, target, spectra)
    
    # Check if gradients can be computed
    loss.backward()
    
    assert predicted.grad is not None
    assert spectra.grad is not None
    assert torch.any(predicted.grad != 0)
    assert torch.any(spectra.grad != 0)

def test_custom_loss_different_base_functions(loss_inputs):
    """Test CustomLoss with different base loss functions"""
    predicted, target, spectra = loss_inputs
    
    # Test with MSE loss
    loss_fn_mse = CustomLoss(base_loss_fn=F.mse_loss)
    mse_loss = loss_fn_mse(predicted, target, spectra)
    
    # Test with L1 loss
    loss_fn_l1 = CustomLoss(base_loss_fn=F.l1_loss)
    l1_loss = loss_fn_l1(predicted, target, spectra)
    
    # Losses should be different but both valid
    assert isinstance(mse_loss, torch.Tensor)
    assert isinstance(l1_loss, torch.Tensor)
    assert mse_loss.item() != l1_loss.item()
