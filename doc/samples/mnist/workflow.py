"""Sample of MNIST training using PyTorch.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

import rflow


class LoadDataset(rflow.Interface):
    def evaluate(self, resource):
        from torchvision import datasets
        datasets.MNIST(resource.filepath, download=True)

        return self.load(resource)

    def load(self, resource):
        from torchvision import datasets, transforms
        train_dataset = datasets.MNIST('data', download=True, train=True,
                                       transform=transforms.Compose([
                                           transforms.ToTensor(),
                                           transforms.Normalize(
                                               (0.1307,), (0.3081,))
                                       ]))
        test_dataset = datasets.MNIST('data', train=False,
                                      transform=transforms.Compose([
                                          transforms.ToTensor(),
                                          transforms.Normalize(
                                              (0.1307,), (0.3081,))
                                      ]))

        return train_dataset, test_dataset


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout2d(0.25)
        self.dropout2 = nn.Dropout2d(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = x.flatten(1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


def train(model, device, train_loader, optimizer, epoch, log_interval):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.item()))


def test(model, device, test_loader):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            # sum up batch loss
            test_loss += F.nll_loss(output, target, reduction='sum').item()
            # get the index of the max log-probability
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)

    accuracy = 100. * correct / len(test_loader.dataset)
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        accuracy))
    return accuracy


# Defines a node
class Train(rflow.Interface):
    # The `evaluate` funtion is every node's execution entry point.
    # Every argument is tracked by rflow (unless if it's specified in `non_collateral`)
    # Node are executed again if the tracked argument changes after the previous run.
    def evaluate(self, resource, train_dataset, test_dataset,
                 batch_size, test_batch_size, epochs, learning_rate=1.0, gamma=0.1,
                 device="cuda:0", log_interval=10):
        """Trains the Mnist model.
        """
        from torch.utils.data import DataLoader
        from torch.optim.lr_scheduler import StepLR
        import torch.optim as optim

        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(
            test_dataset, batch_size=test_batch_size, shuffle=True)
        model = Net().to(device)
        model.train()

        optimizer = optim.Adadelta(model.parameters(), lr=learning_rate)

        scheduler = StepLR(optimizer, step_size=1, gamma=gamma)
        for epoch in range(1, epochs + 1):
            train(model, device, train_loader,
                  optimizer, epoch, log_interval)
            test(model, device, test_loader)
            scheduler.step()

        torch.save(model.cpu(), resource.filepath)
        return model.to(device)

    # When nodes are update, then rflow calls load instead of evaluate.
    def load(self, resource, device):
        """Loads trained model
        """
        return torch.load(resource.filepath).to(device)

    def non_collateral(self):
        """Lists arguments that doesn't change the node's output.
        """
        return ["device", "log_interval"]


class Test(rflow.Interface):
    def non_collateral(self):
        return ["device"]

    def evaluate(self, model, test_dataset, test_batch_size, device):
        device = "cuda:0"
        test_loader = torch.utils.data.DataLoader(test_dataset,
                                                  batch_size=test_batch_size, shuffle=True)
        accuracy = test(model.to(device), device, test_loader)
        self.save_measurement({"Accuracy": accuracy})


@rflow.graph()
def mnist_train(g):
    g.dataset = LoadDataset(rflow.FSResource("data"))

    g.train = Train(rflow.FSResource("model.torch"))
    with g.train as args:
        args.train_dataset = g.dataset[0]
        args.test_dataset = g.dataset[1]
        args.batch_size = 64
        args.test_batch_size = 1000
        args.epochs = 14
        args.learning_rate = 1.0
        args.gamma = 0.1
        args.device = "cuda:0"

    g.test = Test()
    with g.test as args:
        args.model = g.train
        args.test_dataset = g.dataset[1]
        args.test_batch_size = 1000
        args.device = "cuda:0"
