## Setting the priority with UDP sockets

If the packet is an IPv4 packet and the value to be inserted in the ToS field is not null, then the packet is assigned a priority based on such ToS value (according to the ns3::Socket::IpTos2Priority() function). Otherwise, the priority associated with the socket is assigned to the packet.

Setting the priority with TCP sockets

Every packet is assigned a priority equal to the priority associated with the socket.

## Setting the priority with packet sockets

Every packet is assigned a priority equal to the priority associated with the socket.

## 23.4.6 Socket errno

to be completed

## 23.4.7 Example programs

to be completed

## 23.4.8 POSIX-like sockets API

## 23.5 Simple NetDevice

Placeholder chapter

## 23.6 Queues

This section documents the queue object, which is typically used by NetDevices and QueueDiscs to store packets.

Packets stored in a queue can be managed according to different policies. Currently, only the DropTail policy is available.

## 23.6.1 Model Description

The source code for the new module lives in the directory src/network/utils.

The Queue class has been redesigned as a template class object to allow us to instantiate queues storing different types of items. The unique template type parameter specifies the type of items stored in the queue. The only requirement on the item type is that it must provide a GetSize () method which returns the size of the packet included in the item. Currently, queue items can be objects of the following classes:

• Packet

• QueueItem and subclasses (e.g., QueueDiscItem)

## • WifiMacQueueItem

The internal queues of the queue discs are of type Queue<QueueDiscItem> (an alias of which being InternalQueue). A number of network devices (SimpleNetDevice, PointToPointNetDevice, CsmaNetDevice) use a Queue<Packet> to store packets to be transmitted. WifiNetDevices use instead queues of type WifiMacQueue, which is a subclass of Queue storing objects of type WifiMacQueueItem. Other devices, such as WiMax and LTE, use specialized queues.

## Design

The Queue class derives from the QueueBase class, which is a non-template class providing all the methods that are independent of the type of the items stored in the queue. The Queue class provides instead all the operations that depend on the item type, such as enqueue, dequeue, peek and remove. The Queue class also provides the ability to trace certain queue operations such as enqueuing, dequeuing, and dropping.

Queue is an abstract base class and is subclassed for specific scheduling and drop policies. Subclasses need to define the following public methods:

• bool Enqueue (Ptr<Item> item): Enqueue a packet

• Ptr<Item> Dequeue (): Dequeue a packet

• Ptr<Item> Remove (): Remove a packet

• Ptr<const Item> Peek (): Peek a packet

The Enqueue method does not allow to store a packet if the queue capacity is exceeded. Subclasses may also define specialized public methods. For instance, the WifiMacQueue class provides a method to dequeue a packet based on its tid and MAC address.

There are five trace sources that may be hooked:

• Enqueue

• Dequeue

• Drop

• DropBeforeEnqueue

• DropAfterDequeue

Also, the QueueBase class defines two additional trace sources:

• PacketsInQueue

• BytesInQueue

## DropTail

This is a basic first-in-first-out (FIFO) queue that performs a tail drop when the queue is full.

The DropTailQueue class defines one attribute:

• MaxSize: the maximum queue size
