import * as Dialog from "@radix-ui/react-dialog";

export function ConfirmDialog({
  title,
  description,
  onConfirm,
}: {
  title: string;
  description: string;
  onConfirm: () => void;
}) {
  return (
    <Dialog.Root>
      <Dialog.Trigger className="rounded border px-3 py-1 text-sm hover:bg-sky-50">Abrir confirmação</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-80 -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white p-4 shadow-lg">
          <Dialog.Title className="font-semibold">{title}</Dialog.Title>
          <Dialog.Description className="mt-2 text-sm text-ink/70">{description}</Dialog.Description>
          <div className="mt-4 flex justify-end gap-2">
            <Dialog.Close className="rounded border px-3 py-1">Cancelar</Dialog.Close>
            <Dialog.Close
              className="rounded bg-ink px-3 py-1 text-white"
              onClick={() => {
                onConfirm();
              }}
            >
              Confirmar
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
