'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { useToast, ToastProvider } from '@/components/ui/Toast';

function DemoContent() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const { success, error, warning, info } = useToast();

  return (
    <div className="min-h-screen bg-neutral-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <h1 className="text-4xl font-bold text-neutral-900">UI Components Demo</h1>

        {/* Buttons */}
        <Card>
          <h2 className="text-2xl font-semibold mb-4">Buttons</h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="success">Success</Button>
            <Button variant="danger">Danger</Button>
            <Button variant="outline">Outline</Button>
            <Button loading>Loading</Button>
            <Button disabled>Disabled</Button>
          </div>

          <h3 className="text-xl font-semibold mt-6 mb-4">Button Sizes</h3>
          <div className="flex items-end gap-4">
            <Button size="sm">Small</Button>
            <Button size="md">Medium</Button>
            <Button size="lg">Large</Button>
          </div>
        </Card>

        {/* Inputs */}
        <Card>
          <h2 className="text-2xl font-semibold mb-4">Inputs</h2>
          <div className="space-y-4 max-w-md">
            <Input
              label="Email"
              type="email"
              placeholder="Enter your email"
              helperText="We'll never share your email"
            />
            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              required
            />
            <Input
              label="With Error"
              error="This field is required"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
            <Input
              size="sm"
              placeholder="Small input"
            />
            <Input
              size="lg"
              placeholder="Large input"
            />
          </div>
        </Card>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <h3 className="font-semibold">Simple Card</h3>
            <p className="text-neutral-600 mt-2">This is a basic card with default padding.</p>
          </Card>

          <Card
            header={<h3 className="font-semibold">With Header</h3>}
            footer={<Button size="sm">Action</Button>}
          >
            <p className="text-neutral-600">Card with header and footer sections.</p>
          </Card>

          <Card hoverable>
            <h3 className="font-semibold">Hoverable</h3>
            <p className="text-neutral-600 mt-2">Hover over me!</p>
          </Card>
        </div>

        {/* Modal */}
        <Card>
          <h2 className="text-2xl font-semibold mb-4">Modal</h2>
          <Button onClick={() => setIsModalOpen(true)}>Open Modal</Button>

          <Modal
            open={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            title="Example Modal"
            footer={
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={() => setIsModalOpen(false)}>
                  Confirm
                </Button>
              </div>
            }
          >
            <p className="text-neutral-600">
              This is a modal dialog with a title, content, and footer actions.
            </p>
          </Modal>
        </Card>

        {/* Toasts */}
        <Card>
          <h2 className="text-2xl font-semibold mb-4">Toast Notifications</h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="success" onClick={() => success('Operation successful!')}>
              Show Success
            </Button>
            <Button variant="danger" onClick={() => error('Something went wrong!')}>
              Show Error
            </Button>
            <Button variant="outline" onClick={() => warning('Please be careful!')}>
              Show Warning
            </Button>
            <Button variant="primary" onClick={() => info('Here's some information')}>
              Show Info
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function DemoPage() {
  return (
    <ToastProvider>
      <DemoContent />
    </ToastProvider>
  );
}
