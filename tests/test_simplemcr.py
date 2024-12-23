import pytest
import torch
import torch.nn as nn
from torchmcr.simplemcr import SimpleWeights, SimpleSpectra, SimpleMCRModel, NormalizedSpectra, NormalizedSpectraMCRModel
from torchmcr.utils.domain_constraints import normalized_softmax

@pytest.fixture
def sample_dimensions():
    return {
        'M': 10,  # number of samples
        'K': 3,   # number of components
        'N': 20   # number of wavelengths
    }

def test_simple_weights_initialization(sample_dimensions):
    weights = SimpleWeights(sample_dimensions['M'], sample_dimensions['K'])
    assert weights.weight_matrix.shape == (sample_dimensions['M'], sample_dimensions['K'])
    
def test_simple_weights_with_preload():
    preload = torch.ones(5, 2)
    weights = SimpleWeights(5, 2, preload_weights=preload)
    assert torch.equal(weights.weight_matrix, preload)

def test_simple_weights_forward():
    weights = SimpleWeights(5, 2, modifier=nn.Softplus())
    output = weights()
    assert output.shape == (5, 2)
    assert torch.all(output > 0)  # Softplus ensures positive values

def test_simple_spectra_initialization(sample_dimensions):
    spectra = SimpleSpectra(sample_dimensions['K'], sample_dimensions['N'])
    assert spectra.spectra_matrix.shape == (sample_dimensions['K'], sample_dimensions['N'])

def test_simple_spectra_with_preload():
    preload = torch.ones(3, 15)
    spectra = SimpleSpectra(3, 15, preload_spectra=preload)
    assert torch.equal(spectra.spectra_matrix, preload)

def test_simple_spectra_forward():
    spectra = SimpleSpectra(3, 15, modifier=nn.Softplus())
    output = spectra()
    assert output.shape == (3, 15)
    assert torch.all(output > 0)  # Softplus ensures positive values

def test_simple_mcr_model_initialization(sample_dimensions):
    model = SimpleMCRModel(
        sample_dimensions['M'],
        sample_dimensions['K'],
        sample_dimensions['N']
    )
    assert isinstance(model.weights, SimpleWeights)
    assert isinstance(model.spectra, SimpleSpectra)

def test_simple_mcr_model_forward(sample_dimensions):
    model = SimpleMCRModel(
        sample_dimensions['M'],
        sample_dimensions['K'],
        sample_dimensions['N']
    )
    output = model()
    assert output.shape == (sample_dimensions['M'], sample_dimensions['N'])

def test_simple_mcr_model_with_preload():
    preload_weights = torch.ones(5, 2)
    preload_spectra = torch.ones(2, 10)
    model = SimpleMCRModel(
        5, 2, 10,
        preload_weights=preload_weights,
        preload_spectra=preload_spectra
    )
    output = model()
    # With Softplus modifier (default), output won't exactly equal 5
    # but should be close to matrix multiplication of preloaded values
    assert output.shape == (5, 10)
    assert torch.all(output > 0)

def test_simple_mcr_model_without_modifiers():
    preload_weights = torch.ones(5, 2)
    preload_spectra = torch.ones(2, 10)
    model = SimpleMCRModel(
        5, 2, 10,
        preload_weights=preload_weights,
        preload_spectra=preload_spectra,
        weights_modifier=None,
        spectra_modifier=None
    )
    output = model()
    # Without modifiers, output should exactly equal matrix multiplication
    expected = torch.ones(5, 10) * 2  # 5x2 @ 2x10 with all ones = 5x10 with all twos
    assert torch.allclose(output, expected) 

def test_normalized_spectra_initialization(sample_dimensions):
    spectra = NormalizedSpectra(sample_dimensions['K'], sample_dimensions['N'])
    assert spectra.spectra_matrix.shape == (sample_dimensions['K'], sample_dimensions['N'])

def test_normalized_spectra_with_preload():
    preload = torch.ones(3, 15)
    spectra = NormalizedSpectra(3, 15, preload_spectra=preload)
    output = spectra()
    # Check if output sums to 1 along wavelength dimension
    sums = output.sum(dim=1)
    assert torch.allclose(sums, torch.ones_like(sums))

def test_normalized_spectra_forward():
    spectra = NormalizedSpectra(3, 15)
    output = spectra()
    assert output.shape == (3, 15)
    # Check if output is normalized (sums to 1 along wavelength dimension)
    sums = output.sum(dim=1)
    assert torch.allclose(sums, torch.ones_like(sums))
    # Check if all values are positive
    assert torch.all(output >= 0)

def test_normalized_spectra_clipping():
    spectra = NormalizedSpectra(3, 15, clip_low=-10, clip_high=10)
    # Set some extreme values in the internal matrix
    spectra.spectra_matrix.data = torch.randn(3, 15) * 100
    output = spectra()
    # Check if output is still normalized despite clipping
    sums = output.sum(dim=1)
    assert torch.allclose(sums, torch.ones_like(sums))

def test_normalized_mcr_model_initialization(sample_dimensions):
    model = NormalizedSpectraMCRModel(
        sample_dimensions['M'],
        sample_dimensions['K'],
        sample_dimensions['N']
    )
    assert isinstance(model.weights, SimpleWeights)
    assert isinstance(model.spectra, NormalizedSpectra)

def test_normalized_mcr_model_forward(sample_dimensions):
    model = NormalizedSpectraMCRModel(
        sample_dimensions['M'],
        sample_dimensions['K'],
        sample_dimensions['N']
    )
    output = model()
    assert output.shape == (sample_dimensions['M'], sample_dimensions['N'])

def test_normalized_mcr_model_with_preload():
    preload_weights = torch.ones(5, 2)
    preload_spectra = normalized_softmax(torch.ones(2, 10))
    model = NormalizedSpectraMCRModel(
        5, 2, 10,
        preload_weights=preload_weights,
        preload_spectra=preload_spectra
    )
    output = model()
    assert output.shape == (5, 10)
    assert torch.all(output >= 0)

def test_normalized_mcr_model_spectra_normalization():
    model = NormalizedSpectraMCRModel(5, 2, 10)
    # Check if spectra are normalized
    spectra_output = model.spectra()
    sums = spectra_output.sum(dim=1)
    assert torch.allclose(sums, torch.ones_like(sums)) 